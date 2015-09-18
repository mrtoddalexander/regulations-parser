# vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree

from regparser.notice import preprocessors
from tests.xml_builder import XMLBuilderMixin


class MoveLastAMDParTests(XMLBuilderMixin, TestCase):
    def test_improper_amdpar_location(self):
        """The second AMDPAR is in the wrong parent; it should be moved"""
        with self.tree.builder("PART") as part:
            with part.REGTEXT(ID="RT1") as regtext:
                regtext.AMDPAR(u"1. In § 105.1, revise paragraph (b):")
                with regtext.SECTION() as section:
                    section.P("Some Content")
                # Note this has the wrong parent
                regtext.AMDPAR(u"3. In § 105.2, revise paragraph (a) to read:")
            with part.REGTEXT(ID="RT2") as regtext:
                with regtext.SECTION() as section:
                    section.P("Other Content")
        xml = self.tree.render_xml()

        preprocessors.MoveLastAMDPar().transform(xml)

        amd1, amd2 = xml.xpath("//AMDPAR")
        self.assertEqual(amd1.getparent().get("ID"), "RT1")
        self.assertEqual(amd2.getparent().get("ID"), "RT2")

    def test_trick_amdpar_location_diff_parts(self):
        """Similar situation to the above, except the regulations describe
        different parts and hence the AMDPAR should not move"""
        with self.tree.builder("PART") as part:
            with part.REGTEXT(ID="RT1", PART="105") as regtext:
                regtext.AMDPAR(u"1. In § 105.1, revise paragraph (b):")
                with regtext.SECTION() as section:
                    section.P("Some Content")
                regtext.AMDPAR(u"3. In § 105.2, revise paragraph (a) to read:")
            with part.REGTEXT(ID="RT2", PART="107") as regtext:
                with regtext.SECTION() as section:
                    section.P("Other Content")
        xml = self.tree.render_xml()

        preprocessors.MoveLastAMDPar().transform(xml)

        amd1, amd2 = xml.xpath("//AMDPAR")
        self.assertEqual(amd1.getparent().get("ID"), "RT1")
        self.assertEqual(amd2.getparent().get("ID"), "RT1")


class SupplementAMDParTests(XMLBuilderMixin, TestCase):
    def test_incorrect_ps(self):
        """Supplement I AMDPARs are not always labeled as should be"""
        with self.tree.builder("PART") as part:
            with part.REGTEXT() as regtext:
                regtext.AMDPAR(u"1. In § 105.1, revise paragraph (b):")
                with regtext.SECTION() as section:
                    section.STARS()
                    section.P("(b) Content")
                regtext.P("2. In Supplement I to Part 105,")
                regtext.P("A. Under Section 105.1, 1(b), paragraph 2 is "
                          "revised")
                regtext.P("The revisions are as follows")
                regtext.HD("Supplement I to Part 105", SOURCE="HD1")
                regtext.STARS()
                with regtext.P() as p:
                    p.E("1(b) Heading", T="03")
                regtext.STARS()
                regtext.P("2. New Context")
        xml = self.tree.render_xml()

        preprocessors.SupplementAMDPar().transform(xml)

        # Note that the SECTION paragraphs were not converted
        self.assertEqual(
            [amd.text for amd in xml.xpath("//AMDPAR")],
            [u"1. In § 105.1, revise paragraph (b):",
             "2. In Supplement I to Part 105,",
             "A. Under Section 105.1, 1(b), paragraph 2 is revised",
             "The revisions are as follows"])


class ParenthesesCleanupTests(XMLBuilderMixin, TestCase):
    def assert_transformed(self, original, new_text):
        """Helper function to verify that the XML is transformed as
        expected"""
        self.setUp()
        with self.tree.builder("PART") as part:
            part.P(_xml=original)
        xml = self.tree.render_xml()
        preprocessors.ParenthesesCleanup().transform(xml)
        self.assertEqual("<P>{}</P>".format(new_text),
                         etree.tostring(xml[0]))

    def test_transform(self):
        """The parens should always move out"""
        expected = '(<E T="03">a</E>) Content'
        self.assert_transformed('(<E T="03">a</E>) Content', expected)
        self.assert_transformed('(<E T="03">a)</E> Content', expected)
        self.assert_transformed('<E T="03">(a</E>) Content', expected)
        self.assert_transformed('<E T="03">(a)</E> Content', expected)
        self.assert_transformed('<E T="03">Paragraph 22(a)(5)</E> Content',
                                '<E T="03">Paragraph 22(a)(5)</E> Content')


class ApprovalsFPTests(XMLBuilderMixin, TestCase):
    def control_number(self, number, prefix="Approved"):
        return ("({} by the Office of Management and Budget under "
                "control number {})".format(prefix, number))

    def test_transform(self):
        """Verify that FP tags get transformed, but only if they match a
        certain string"""
        with self.tree.builder("PART") as part:
            part.APPRO(self.control_number('1111-2222'))
            part.FP("Something else")
            part.FP(self.control_number('2222-4444'))
            part.P(self.control_number('3333-6666'))
            with part.EXTRACT() as extract:
                extract.FP(self.control_number(
                    "4444-8888", "Paragraph (b)(2) approved"))
            part.P(self.control_number('4444-8888'))
        xml = self.tree.render_xml()
        preprocessors.ApprovalsFP().transform(xml)
        appros = [appro.text for appro in xml.xpath("./APPRO")]
        self.assertEqual(appros, [
            self.control_number('1111-2222'), self.control_number('2222-4444'),
            self.control_number('4444-8888', 'Paragraph (b)(2) approved')])
