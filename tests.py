import unittest
import json
import os
from app import app
import database

class NutriTrackAPITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override the database path to use a test database
        database.DB_PATH = 'health_test.db'
        cls.client = app.test_client()
        cls.client.testing = True

    def setUp(self):
        # Clean up and re-initialize DB before each test
        if os.path.exists(database.DB_PATH):
            os.remove(database.DB_PATH)
        database.init_db()

    def tearDown(self):
        if os.path.exists(database.DB_PATH):
            os.remove(database.DB_PATH)

    def test_search_foods(self):
        response = self.client.get('/api/foods/search?q=Apple')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['name'], 'Apple (1 medium)')

    def test_add_and_get_logs(self):
        # Add a log
        payload = {
            'date': '2023-10-10',
            'food_id': 1,
            'servings': 2.0,
            'meal_type': 'Breakfast'
        }
        response = self.client.post('/api/logs', json=payload)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Get logs
        response = self.client.get('/api/logs?date=2023-10-10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['logs']), 1)
        self.assertEqual(data['logs'][0]['servings'], 2.0)
        
    def test_invalid_log_submission(self):
        # Missing required fields
        payload = {
            'date': '2023-10-10',
            'food_id': 1
        }
        response = self.client.post('/api/logs', json=payload)
        self.assertEqual(response.status_code, 400)
        
        # Invalid data type
        payload = {
            'date': '2023-10-10',
            'food_id': 'NOT_AN_ID',
            'servings': -5,
            'meal_type': 'FakeMeal'
        }
        response = self.client.post('/api/logs', json=payload)
        self.assertEqual(response.status_code, 400)

    def test_insights_generation(self):
        response = self.client.get('/api/insights?date=2023-10-10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('health_score', data)
        self.assertIn('trends', data)
        self.assertIn('favorite_food', data)

    def test_water_tracking(self):
        # Add water
        response = self.client.post('/api/water', json={'date': '2023-10-10', 'glasses': 4})
        self.assertEqual(response.status_code, 200)
        
        # Get water
        response = self.client.get('/api/water?date=2023-10-10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['glasses'], 4)

if __name__ == '__main__':
    unittest.main()
