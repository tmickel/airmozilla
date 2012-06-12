from django.contrib.auth.models import User, Group
from django.test import TestCase


from funfactory.urlresolvers import reverse

from nose.tools import eq_


class TestPermissions(TestCase):
    def _staff_login(self, is_staff=True):
        u = User.objects.create_user('fake', 'fake@fake.com', 'fake')
        u.is_staff = is_staff
        u.save()
        self.client.login(username='fake', password='fake')
        return u

    def test_unauthorized(self):
        """ Client with no log in - should be rejected. """
        response = self.client.get(reverse('manage.home'))
        eq_(response.status_code, 302)

    def test_not_staff(self):
        """ User is not staff - should be rejected. """
        self._staff_login(False)
        response = self.client.get(reverse('manage.home'))
        eq_(response.status_code, 302)

    def test_staff_home(self):
        """ User is staff - should get an OK homepage. """
        self._staff_login()
        response = self.client.get(reverse('manage.home'))
        eq_(response.status_code, 200)

    def test_staff_logout(self):
        """ Log out makes admin inaccessible. """
        self._staff_login()
        self.client.get(reverse('auth.logout'))
        response = self.client.get(reverse('manage.home'))
        eq_(response.status_code, 302)

    def test_edit_user(self):
        """ Unprivileged admin - shouldn't see user change page. """
        self._staff_login()
        response = self.client.get(reverse('manage.users'))
        eq_(response.status_code, 302)


class TestUsersAndGroups(TestCase):
    def setUp(self):
        User.objects.create_superuser('fake', 'fake@fake.com', 'fake')
        self.client.login(username='fake', password='fake')

    def test_user_edit(self):
        """ Add superuser and staff status via the user edit form. """
        user = User.objects.create_user('no', 'no@no.com', 'no')
        response = self.client.post(reverse('manage.user_edit',
                                            kwargs={'id': user.id}),
            {
                'is_superuser': 'on',
                'is_staff': 'on',
                'is_active': 'on'
            }
        )
        eq_(response.status_code, 302)
        user = User.objects.get(id=user.id)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_group_add(self):
        """ Add a group. """
        response = self.client.post(reverse('manage.group_new'),
            {
                'name': 'fake_group'
            }
        )
        eq_(response.status_code, 302)

        group = Group.objects.get(name='fake_group')
        self.assertTrue(group is not None)
        self.assertTrue(group.name == 'fake_group')
