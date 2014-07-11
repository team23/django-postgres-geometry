from django.test import TestCase, SimpleTestCase
from django.utils import six
from django.db import models, connection
from django.core.exceptions import FieldError
from mock import Mock

from .fields import Point, PointField, SegmentPathField, PolygonField


class TestModel(models.Model):

    point = PointField(null=True)
    segment_path = SegmentPathField(null=True)
    polygon = PolygonField(null=True)


class PointTests(SimpleTestCase):

    def test_from_string(self):
        values = (
            ('(1,1)', Point(1, 1)),
            ('(-1,1)', Point(-1, 1)),
            ('(1,-1)', Point(1, -1)),
            ('(-1,-1)', Point(-1, -1)),

            ('(1.5,1.5)', Point(1.5, 1.5)),
            ('(-1.5,1.5)', Point(-1.5, 1.5)),
            ('(1.5,-1.5)', Point(1.5, -1.5)),
            ('(-1.5,-1.5)', Point(-1.5, -1.5)),

            ('(.5,.5)', Point(0.5, 0.5)),
            ('(-.5,.5)', Point(-0.5, 0.5)),
            ('(.5,-.5)', Point(0.5, -0.5)),
            ('(-.5,-.5)', Point(-0.5, -0.5)),
        )

        for value_str, expected in values:
            value = Point.from_string(value_str)

            self.assertEqual(value, expected, (value_str, value, expected))

    def test_eq(self):
        self.assertTrue(Point(1, 1) == Point(1, 1))
        self.assertFalse(Point(1, 1) != Point(1, 1))
        self.assertTrue(Point(1, 1) != Point(2, 1))
        self.assertTrue(Point(1, 1) != Point(1, 2))
        self.assertTrue(Point(1, 1) != Point(2, 2))


class GeometryFieldTestsMixin(object):

    def test_db_type(self):
        self.assertEqual(self.field().db_type(connection), self.db_type)

    def test_postgres_connection(self):
        m_connection = Mock()
        m_connection.settings_dict = {'ENGINE': 'psycopg2'}

        self.assertIsInstance(
            self.field().db_type(m_connection), six.string_types)

    def test_non_postgres_connection(self):
        m_connection = Mock()
        m_connection.settings_dict = {'ENGINE': 'sqlite'}

        self.assertRaises(FieldError, self.field().db_type, m_connection)


class SegmentPathFieldTests(GeometryFieldTestsMixin, TestCase):

    field = SegmentPathField
    db_type = 'path'

    def test_store_field(self):
        value = [Point(1, 1), Point(2, 2)]

        model = TestModel()
        model.segment_path = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertIsInstance(model.segment_path, list)
        self.assertEqual(model.segment_path, value)


class PolygonFieldTests(GeometryFieldTestsMixin, TestCase):

    field = PolygonField
    db_type = 'polygon'

    def test_store_field(self):
        value = [Point(1, 1), Point(2, 2), Point(1, 1)]

        model = TestModel()
        model.polygon = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertIsInstance(model.polygon, list)
        self.assertEqual(model.polygon, value)

    def test_non_closed_polygon(self):
        """
        First and last points on a polygon must be equal
        """
        model = TestModel()
        model.polygon = [Point(1, 1), Point(2, 2)]

        with self.assertRaisesRegexp(ValueError, 'Not self-closing polygon'):
            model.save()


class PointFieldTests(GeometryFieldTestsMixin, TestCase):

    field = PointField
    db_type = 'point'

    def test_store_field(self):
        value = Point(1, 1)

        model = TestModel()
        model.point = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertEqual(model.point, value)