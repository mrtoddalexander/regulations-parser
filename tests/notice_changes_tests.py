# -*- coding: utf-8 -*-
from unittest import TestCase

import six

from regparser.notice import changes
from regparser.notice.amdparser import Amendment
from regparser.test_utils.xml_builder import XMLBuilder
from regparser.tree.struct import Node, find


class ChangesTests(TestCase):
    def build_tree(self):
        n1 = Node('n1', label=['200', '1'])
        n2 = Node('n1i', label=['200', 1, 'i'])
        n3 = Node('n2', label=['200', '2'])
        n4 = Node('n3', label=['200', '3'])
        n5 = Node('n3a', label=['200', '3', 'a'])

        n1.children = [n2]
        n4.children = [n5]
        root = Node('root', label=['200'], children=[n1, n3, n4])
        return root

    def test_find_candidate(self):
        root = self.build_tree()
        result = changes.find_candidate(root, 'i', [])[0]
        self.assertEqual(u'n1i', result.text)

        n2c = Node('n3c', label=['200', '2', 'i', 'i'])
        n2 = find(root, '200-2')
        n2.children = [n2c]

        result = changes.find_candidate(root, 'i', [])[0]
        self.assertEqual(result.label, ['200', '2', 'i', 'i'])

    def test_not_find_candidate(self):
        root = self.build_tree()
        result = changes.find_candidate(root, 'j', [])
        self.assertEqual(result, [])

    def test_find_candidate_impossible_label(self):
        n1 = Node('', label=['200', '1'])
        n1a = Node('', label=['200', '1', 'a'])

        n1a1i = Node('', label=['200', '1', 'a', '1', 'i'])
        n1a.children = [n1a1i]

        n1b = Node('', label=['200', '1', 'b'])
        n1i = Node('', label=['200', '1', 'i'])
        n1.children = [n1a, n1b, n1i]

        root = Node('root', label=['200'], children=[n1])
        candidate = changes.find_candidate(
            root, 'i', ['200-1-a', '200-1-b'])[0]

        self.assertEqual(candidate.label, ['200', '1', 'i'])

    def test_find_misparsed_node(self):
        n2 = Node('n1i', label=['200', 1, 'i'])
        root = self.build_tree()

        result = {'action': 'PUT'}

        result = changes.find_misparsed_node(root, 'i', result, [])
        self.assertEqual(result['action'], 'PUT')
        self.assertTrue(result['candidate'])
        self.assertEqual(result['node'], n2)

    def test_create_add_amendment(self):
        root = self.build_tree()

        amendment = {'node': root, 'action': 'POST'}
        amendments = changes.create_add_amendment(amendment)
        self.assertEqual(6, len(amendments))

        amends = {}
        for a in amendments:
            amends.update(a)

        for l in ['200-1-i', '200-1', '200-2', '200-3-a', '200-3', '200']:
            self.assertTrue(l in amends)

        for label, node in amends.items():
            self.assertEqual(label, '-'.join(node['node']['label']))
            self.assertEqual(node['action'], 'POST')
            self.assertFalse('children' in node['node'])

    def test_create_add_amendment_parent_label(self):
        """If an amendment has an explicit parent_label, it should only be
        applied to the root of the tree"""
        root = self.build_tree()
        amendment = {'node': root, 'action': 'POST',
                     'parent_label': ['arbitrary']}
        amendments = changes.create_add_amendment(amendment)
        self.assertEqual(6, len(amendments))
        amends = {}
        for a in amendments:
            amends.update(a)

        self.assertEqual(amends['200'].get('parent_label'), ['arbitrary'])
        for label, change in amends.items():
            if label == '200':
                self.assertEqual(change['parent_label'], ['arbitrary'])
            else:
                self.assertFalse('parent_label' in change)

    def test_flatten_tree(self):
        tree = self.build_tree()

        node_list = []
        changes.flatten_tree(node_list, tree)

        self.assertEqual(6, len(node_list))
        for n in node_list:
            self.assertEqual(n.children, [])

    def test_resolve_candidates(self):
        amend_map = {}

        n1 = Node('n1', label=['200', '1'])
        amend_map['200-1-a'] = [{'node': n1, 'candidate': False}]

        n2 = Node('n2', label=['200', '2', 'i'])
        amend_map['200-2-a-i'] = [{'node': n2, 'candidate': True}]

        self.assertNotEqual(
            amend_map['200-2-a-i'][0]['node'].label_id(),
            '200-2-a-i')

        changes.resolve_candidates(amend_map)

        self.assertEqual(
            amend_map['200-2-a-i'][0]['node'].label_id(),
            '200-2-a-i')

    def test_resolve_candidates_accounted_for(self):
        amend_map = {}

        n1 = Node('n1', label=['200', '1'])
        amend_map['200-1-a'] = [{'node': n1, 'candidate': False}]

        n2 = Node('n2', label=['200', '2', 'i'])

        amend_map['200-2-a-i'] = [{'node': n2, 'candidate': True}]
        amend_map['200-2-i'] = [{'node': n2, 'candidate': False}]

        changes.resolve_candidates(amend_map, warn=False)
        self.assertEqual(2, len(amend_map.keys()))

    def test_resolve_candidates_double_delete(self):
        """In the unfortunate case where *two* candidates are wrong make
        sure we don't blow up"""
        amend_map = {}

        n1 = Node('n1', label=['200', '1', 'i'])
        n2 = Node('n2', label=['200', '1', 'i'])
        amend_map['200-1-a-i'] = [{'node': n1, 'candidate': True},
                                  {'node': n2, 'candidate': True}]
        amend_map['200-1-i'] = []
        changes.resolve_candidates(amend_map, warn=False)
        self.assertEqual(1, len(amend_map.keys()))

    def test_match_labels_and_changes_move(self):
        labels_amended = [Amendment('MOVE', '200-?-1', '200-?-2')]
        amend_map = changes.match_labels_and_changes(labels_amended, None)
        self.assertEqual(dict(amend_map), {
            '200-1': [{'action': 'MOVE', 'destination': ['200', '2'],
                       'amdpar_xml': None}]})

    def test_match_labels_and_changes_delete(self):
        labels_amended = [Amendment('DELETE', '200-?-1-a-i')]
        amend_map = changes.match_labels_and_changes(labels_amended, None)
        self.assertEqual(dict(amend_map), {
            '200-1-a-i': [{'action': 'DELETE', 'amdpar_xml': None}]})

    def test_match_labels_and_changes_reserve(self):
        labels_amended = [Amendment('RESERVE', '200-?-2-a')]
        amend_map = changes.match_labels_and_changes(
            labels_amended, self.section_node())
        six.assertCountEqual(self, ['200-2-a'], amend_map.keys())

        amendments = amend_map['200-2-a']
        self.assertEqual(amendments[0]['action'], 'RESERVE')
        self.assertEqual(
            amendments[0]['node'], Node('n2a', label=['200', '2', 'a']))

    def section_node(self):
        n1 = Node('n2', label=['200', '2'])
        n2 = Node('n2a', label=['200', '2', 'a'])

        n1.children = [n2]
        root = Node('root', label=['200'], children=[n1])
        return root

    def test_match_labels_and_changes(self):
        labels_amended = [Amendment('POST', '200-?-2'),
                          Amendment('PUT', '200-?-2-a')]

        amend_map = changes.match_labels_and_changes(
            labels_amended, self.section_node())

        self.assertEqual(2, len(amend_map.keys()))

        for label, amendments in amend_map.items():
            amend = amendments[0]
            self.assertFalse(amend['candidate'])
            self.assertTrue(amend['action'] in ['POST', 'PUT'])

    def test_match_labels_and_changes_candidate(self):
        labels_amended = [
            Amendment('POST', '200-?-2'),
            Amendment('PUT', '200-?-2-a-1-i')]

        n1 = Node('n2', label=['200', '2'])
        n2 = Node('n2a', label=['200', '2', 'i'])

        n1.children = [n2]
        root = Node('root', label=['200'], children=[n1])

        amend_map = changes.match_labels_and_changes(
            labels_amended, root)

        self.assertTrue(amend_map['200-2-a-1-i'][0]['candidate'])
        self.assertTrue(
            amend_map['200-2-a-1-i'][0]['node'].label_id(), '200-2-a-1-i')

    def test_bad_label(self):
        label = ['205', '4', 'a', '1', 'ii', 'A']
        node = Node('text', label=label, node_type=Node.REGTEXT)
        self.assertFalse(changes.bad_label(node))

        node.label = ['205', '38', 'i', 'vii', 'A']
        self.assertTrue(changes.bad_label(node))

        node.label = ['205', 'ii']
        self.assertTrue(changes.bad_label(node))

        node.label = ['205', '38', 'A', 'vii', 'A']
        self.assertTrue(changes.bad_label(node))

    def test_impossible_label(self):
        amended_labels = ['205-35-c-1', '205-35-c-2']
        node = Node('', label=['205', '35', 'v'])
        self.assertTrue(changes.impossible_label(node, amended_labels))

        node = Node('', label=['205', '35', 'c', '1', 'i'])
        self.assertFalse(changes.impossible_label(node, amended_labels))

    def test_pretty_changes(self):
        """Verify the output for a variety of "changes" """
        self.assertEqual(
            changes.pretty_change({'action': 'DELETE'}), 'Deleted')
        self.assertEqual(
            changes.pretty_change({'action': 'RESERVE'}), 'Reserved')
        self.assertEqual(
            changes.pretty_change({'action': 'KEEP'}),
            'Mentioned but not modified')
        self.assertEqual(
            changes.pretty_change({'action': 'DESIGNATE',
                                   'destination': ['123', '43', 'a', '2']}),
            'Moved to 123-43-a-2')

        node = {'text': 'Some Text'}
        change = {'action': 'PUT', 'node': node}
        self.assertEqual(
            changes.pretty_change(change), 'Modified: Some Text')

        change['action'] = 'POST'
        self.assertEqual(
            changes.pretty_change(change), 'Added: Some Text')

        node['title'] = 'A Title'
        self.assertEqual(
            changes.pretty_change(change), 'Added (title: A Title): Some Text')

        change['action'] = 'PUT'
        self.assertEqual(
            changes.pretty_change(change),
            'Modified (title: A Title): Some Text')

        change['field'] = '[title]'
        self.assertEqual(
            changes.pretty_change(change), 'Title changed to: A Title')

        del node['title']
        change['field'] = '[a field]'
        self.assertEqual(
            changes.pretty_change(change), 'A Field changed to: Some Text')

    def test_new_subpart_added(self):
        amended_label = Amendment('POST', '200-Subpart:B')
        self.assertTrue(changes.new_subpart_added(amended_label))

        amended_label = Amendment('PUT', '200-Subpart:B')
        self.assertFalse(changes.new_subpart_added(amended_label))

        amended_label = Amendment('POST', '200-Subpart:B-a-3')
        self.assertFalse(changes.new_subpart_added(amended_label))

    def test_find_subpart(self):
        with XMLBuilder("REGTEXT", PART='105', TITLE='12') as ctx:
            ctx.AMDPAR("6. Add subpart B to read as follows:")
            with ctx.SUBPART():
                ctx.HD(u"Subpart B—Requirements", SOURCE="HED")
                with ctx.SECTION():
                    ctx.SECTNO("105.30")
                    ctx.SUBJECT("First In New Subpart")
                    ctx.P("For purposes of this subpart, the follow apply:")
                    ctx.P('(a) "Agent" means agent.')

        amdpar_xml = ctx.xml.xpath('//AMDPAR')[0]
        subpart = changes.find_subpart(amdpar_xml)
        self.assertTrue(subpart is not None)

        headings = [s for s in subpart if s.tag == 'HD']
        self.assertEqual(headings[0].text, u"Subpart B—Requirements")

    def test_fix_section_node(self):
        with XMLBuilder("REGTEXT") as ctx:
            ctx.P("paragraph 1")
            ctx.P("paragraph 2")
        paragraphs = [p for p in ctx.xml if p.tag == 'P']

        with XMLBuilder("REGTEXT") as ctx:
            with ctx.SECTION():
                ctx.SECTNO(" 205.4 ")
                ctx.SUBJECT("[Corrected]")
            ctx.AMDPAR(u"3. In § 105.1, revise paragraph (b) to read as "
                       u"follows:")
        par = ctx.xml.xpath('//AMDPAR')[0]
        section = changes.fix_section_node(paragraphs, par)
        self.assertNotEqual(None, section)
        section_paragraphs = [p for p in section if p.tag == 'P']
        self.assertEqual(2, len(section_paragraphs))

        self.assertEqual(section_paragraphs[0].text, 'paragraph 1')
        self.assertEqual(section_paragraphs[1].text, 'paragraph 2')


class NoticeChangesTests(TestCase):
    def test_update_duplicates(self):
        nc = changes.NoticeChanges()
        nc.add_changes(None, {'123-12': {'action': 'DELETE'},
                              '123-22': {'action': 'OTHER'}})
        nc.add_changes(None, {'123-12': {'action': 'DELETE'}})
        nc.add_changes(None, {'123-12': {'action': 'OTHER'}})
        nc.add_changes(None, {'123-22': {'action': 'OTHER'},
                              '123-32': {'action': 'LAST'}})

        data = nc.changes_by_xml[None]
        self.assertTrue('123-12' in data)
        self.assertTrue('123-22' in data)
        self.assertTrue('123-32' in data)

        self.assertEqual(data['123-12'],
                         [{'action': 'DELETE'}, {'action': 'OTHER'}])
        self.assertEqual(data['123-22'], [{'action': 'OTHER'}])
        self.assertEqual(data['123-32'], [{'action': 'LAST'}])
