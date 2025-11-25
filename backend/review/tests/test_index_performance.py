"""
Performance test for ReviewHistory index optimization

Tests INSERT performance with current (4 indexes) vs optimized (2 indexes) configuration.
"""
import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from content.models import Content, Category
from review.models import ReviewHistory

User = get_user_model()


class IndexPerformanceTest(TestCase):
    """Test ReviewHistory INSERT performance with different index configurations"""

    def setUp(self):
        """Create test user and content"""
        self.user = User.objects.create_user(
            email="perf@test.com",
            password="testpass123",
            username="perftest"
        )

        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )

        self.content = Content.objects.create(
            title="Test Content",
            content="Test content body",
            category=self.category,
            author=self.user
        )

    def test_bulk_insert_performance(self):
        """Test INSERT performance with bulk data"""
        num_records = 10000
        batch_size = 1000

        print(f"\n{'='*60}")
        print(f"Testing ReviewHistory INSERT performance")
        print(f"Records: {num_records:,} | Batch size: {batch_size}")
        print(f"{'='*60}\n")

        # Measure INSERT time
        start_time = time.time()

        for batch_num in range(num_records // batch_size):
            batch = []
            for i in range(batch_size):
                result = ["remembered", "partial", "forgot"][i % 3]
                batch.append(
                    ReviewHistory(
                        content=self.content,
                        user=self.user,
                        result=result,
                        time_spent=30 + (i % 100),
                        notes=f"Test note {batch_num * batch_size + i}"
                    )
                )

            ReviewHistory.objects.bulk_create(batch)

            elapsed = time.time() - start_time
            records_so_far = (batch_num + 1) * batch_size
            rate = records_so_far / elapsed

            print(f"Batch {batch_num + 1}/{num_records // batch_size}: "
                  f"{records_so_far:,} records | "
                  f"{elapsed:.2f}s | "
                  f"{rate:.0f} records/sec")

        total_time = time.time() - start_time
        final_rate = num_records / total_time

        print(f"\n{'='*60}")
        print(f"FINAL RESULTS:")
        print(f"Total records: {num_records:,}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average rate: {final_rate:.0f} records/sec")
        print(f"Time per record: {(total_time / num_records) * 1000:.2f} ms")
        print(f"{'='*60}\n")

        # Verify count
        count = ReviewHistory.objects.count()
        self.assertEqual(count, num_records)

    def test_single_insert_with_timing(self):
        """Test single INSERT performance (simulates actual POST request)"""
        num_iterations = 100

        print(f"\n{'='*60}")
        print(f"Testing single INSERT performance (POST request simulation)")
        print(f"Iterations: {num_iterations}")
        print(f"{'='*60}\n")

        times = []

        for i in range(num_iterations):
            start = time.perf_counter()

            ReviewHistory.objects.create(
                content=self.content,
                user=self.user,
                result=["remembered", "partial", "forgot"][i % 3],
                time_spent=30,
                notes=f"Single insert test {i}"
            )

            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"Average INSERT time: {avg_time:.2f} ms")
        print(f"Min: {min_time:.2f} ms | Max: {max_time:.2f} ms")
        print(f"{'='*60}\n")

        # Performance assertion (should be under 50ms on average)
        self.assertLess(avg_time, 50,
                       f"Average INSERT time {avg_time:.2f}ms exceeds 50ms threshold")
