from django.test import TestCase
from django.urls import reverse
from erp.models import SalesOrder, SalesOrderItem
from django.contrib.auth.models import User

class SalesOrderCreateViewTest(TestCase):
    def setUp(self):
        # Create a user if your view requires authentication
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        
        # URL for the view
        self.url = reverse('saleorder-create-form')  # Ensure you are using the correct name
        
        # Create any necessary data
        # In this case, I'm creating a test user and logging in as that user
        self.client.login(username='testuser', password='testpassword')

    def test_create_sales_order_valid(self):
        """Test submitting valid sales order and formset data"""
        # Data for SalesOrder and SalesOrderItem
        sales_order_data = {
            'order_number': 'SO12345',
            'customer': 1,  # Assuming you have a customer with id 1
            'order_date': '2025-03-04',
            'requested_delivery': '2025-03-10',
            'status': 'DRAFT',
        }

        # Data for SalesOrderItem formset
        sales_order_item_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-quantity': 10,
            'form-0-unit_price': 20.0,
            'form-0-discount_percentage': 10,
            'form-1-quantity': 5,
            'form-1-unit_price': 50.0,
            'form-1-discount_percentage': 5,
        }
        
        # Combine the sales order data and formset data
        data = {**sales_order_data, **sales_order_item_data}
        
        # Send POST request to create a sales order and sales order items
        response = self.client.post(self.url, data)
        
        # Print debugging information to track what's happening
        print(response.status_code)  # Check status code
        print(response.content)  # Check if there are any error messages or forms
        # Ensure the response is a redirect after form is valid
        self.assertRedirects(response, reverse('salesorder-list'))

        # Verify that the SalesOrder and SalesOrderItems were created
        self.assertEqual(SalesOrder.objects.count(), 1)
        sales_order = SalesOrder.objects.first()
        self.assertEqual(sales_order.total_amount, 10 * 20 * (100 - 10) / 100 + 5 * 50 * (100 - 5) / 100)

        self.assertEqual(SalesOrderItem.objects.count(), 2)