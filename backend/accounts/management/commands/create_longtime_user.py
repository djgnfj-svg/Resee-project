from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import random

from accounts.models import Subscription
from content.models import Content
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a longtime learner test account with realistic data'

    def handle(self, *args, **options):
        self.stdout.write('Creating longtime learner test account...')

        # Delete existing user if exists
        email = 'longtime_learner@example.com'
        password = 'longtime123!'

        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            # Delete related objects first
            Subscription.objects.filter(user=existing_user).delete()
            Content.objects.filter(author=existing_user).delete()
            existing_user.delete()

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password
        )
        user.is_email_verified = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f'✓ Created user: {email}'))

        # Create PRO subscription (6 months ago) - use update_or_create to handle existing
        subscription, created = Subscription.objects.update_or_create(
            user=user,
            defaults={
                'tier': 'PRO',
                'is_active': True,
                'start_date': timezone.now() - timedelta(days=180),
                'end_date': timezone.now() + timedelta(days=180)
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Created PRO subscription'))

        # Content templates with various subjects (title max: 30 chars)
        content_templates = [
            # Programming (subjective mode for AI evaluation - needs 200+ chars)
            {'title': 'Polymorphism in OOP',
             'content': 'Polymorphism allows objects of different classes to be treated as objects of a common parent class. It enables method overriding and interface implementation. This is a fundamental concept in object-oriented programming that allows for code reusability and flexibility in software design patterns.',
             'mode': 'subjective'},
            {'title': 'Stack vs Heap Memory',
             'content': 'Stack: automatic memory management, LIFO structure, stores local variables and function call information, faster access due to contiguous allocation. Heap: dynamic memory management, manual allocation and deallocation required, stores objects and data structures, slower access but more flexible size management. Understanding the difference is crucial for memory optimization.',
             'mode': 'subjective'},
            {'title': 'Closures in JavaScript',
             'content': 'A closure is a function that has access to variables in its outer (enclosing) function scope, even after the outer function has returned. This powerful feature enables data privacy, function factories, and maintains state in functional programming patterns. Closures are widely used in JavaScript for callbacks, event handlers, and module patterns.',
             'mode': 'subjective'},
            {'title': 'Virtual DOM Concept',
             'content': 'Virtual DOM is a lightweight copy of the actual DOM maintained in memory. React uses it to enable efficient updates by comparing changes between the virtual and real DOM, then only updating what changed. This reconciliation process significantly improves performance in complex web applications by minimizing expensive DOM manipulation operations.',
             'mode': 'subjective'},
            {'title': 'REST API Principles',
             'content': 'REST (Representational State Transfer) architecture uses standard HTTP methods (GET, POST, PUT, DELETE), maintains stateless communication between client and server, employs resource-based URLs for intuitive navigation, and leverages standard HTTP status codes for clear error handling. These principles create scalable and maintainable web services.',
             'mode': 'subjective'},

            # History (objective mode - shorter)
            {'title': 'World War II End Date',
             'content': 'World War II ended on September 2, 1945, when Japan formally surrendered aboard the USS Missouri.',
             'mode': 'objective'},
            {'title': 'First US President',
             'content': 'George Washington was the first president of the United States, serving from 1789 to 1797.',
             'mode': 'objective'},
            {'title': 'Berlin Wall Fall',
             'content': 'The Berlin Wall fell in 1989, marking the end of the Cold War era.',
             'mode': 'objective'},

            # Science (subjective mode)
            {'title': 'Photosynthesis Process',
             'content': 'Photosynthesis is the biochemical process by which plants, algae, and some bacteria convert light energy into chemical energy stored in glucose molecules. Using chlorophyll, they absorb sunlight and combine carbon dioxide from the air with water from the soil, producing glucose for energy and releasing oxygen as a byproduct. This process is fundamental to life on Earth.',
             'mode': 'subjective'},
            {'title': 'Speed of Light',
             'content': 'The speed of light in a vacuum is exactly 299,792,458 meters per second, approximately 300,000 kilometers per second. This fundamental physical constant is denoted by the symbol "c" and represents the maximum speed at which information and matter can travel through space. Einstein\'s theory of relativity is built upon this principle.',
             'mode': 'subjective'},
            {'title': 'Newton\'s First Law',
             'content': 'Newton\'s First Law of Motion, also known as the law of inertia, states that an object at rest stays at rest and an object in motion stays in motion with the same speed and direction unless acted upon by an unbalanced external force. This principle explains why passengers lurch forward when a car suddenly brakes.',
             'mode': 'subjective'},

            # Language (objective mode)
            {'title': 'What is Palindrome?',
             'content': 'A palindrome is a word, phrase, number, or sequence that reads the same backward as forward, such as "radar", "level", or "A man a plan a canal Panama".',
             'mode': 'objective'},
            {'title': 'Define Ubiquitous',
             'content': 'Ubiquitous means present, appearing, or found everywhere; omnipresent. Example: Smartphones have become ubiquitous in modern society.',
             'mode': 'objective'},
        ]

        # Generate more variations by repeating patterns
        additional_templates = []

        # Programming topics
        programming_topics = [
            ('What is dependency injection?', 'subjective'),
            ('Explain async/await', 'subjective'),
            ('Difference == vs ===', 'objective'),
            ('What is database index?', 'subjective'),
            ('Explain SOLID principles', 'subjective'),
            ('HTTP vs HTTPS difference', 'objective'),
            ('What is race condition?', 'subjective'),
            ('Explain MVC pattern', 'subjective'),
            ('What is Big O notation?', 'subjective'),
            ('SQL vs NoSQL difference', 'objective'),
        ]

        for title, mode in programming_topics:
            if mode == 'subjective':
                content_text = f'{title} - This is a fundamental concept in software development that requires deep understanding. ' + \
                              'Developers must master this principle to write efficient, maintainable, and scalable code. ' + \
                              'Understanding the theoretical foundations as well as practical applications is crucial for professional growth in the field of computer science and software engineering.'
            else:
                content_text = f'{title} - Brief explanation of the concept with key points and practical examples.'

            additional_templates.append({
                'title': title,
                'content': content_text,
                'mode': mode
            })

        # Science topics
        science_topics = [
            ('What is DNA?', 'subjective'),
            ('Explain water cycle', 'subjective'),
            ('What is gravity?', 'subjective'),
            ('Atomic structure', 'objective'),
            ('What is evolution?', 'subjective'),
            ('Speed vs velocity', 'objective'),
            ('What is osmosis?', 'subjective'),
            ('What is entropy?', 'subjective'),
            ('Radioactive decay', 'objective'),
            ('The periodic table', 'objective'),
        ]

        for title, mode in science_topics:
            if mode == 'subjective':
                content_text = f'{title} - This scientific concept is essential for understanding natural phenomena and the physical world around us. ' + \
                              'Scientists have studied this extensively through observation, experimentation, and theoretical models. ' + \
                              'Mastering this knowledge helps us comprehend complex systems and make informed decisions about our environment and health.'
            else:
                content_text = f'{title} - Key scientific facts and principles explained clearly with examples.'

            additional_templates.append({
                'title': title,
                'content': content_text,
                'mode': mode
            })

        # History topics
        history_topics = [
            ('Declaration of Independence', 'objective'),
            ('Printing press inventor', 'objective'),
            ('Industrial Revolution', 'subjective'),
            ('Fall of Roman Empire', 'objective'),
            ('Who was Napoleon?', 'subjective'),
            ('What was Cold War?', 'subjective'),
            ('Moon landing date', 'objective'),
            ('The Renaissance period', 'subjective'),
            ('Communist Manifesto author', 'objective'),
            ('The Silk Road', 'subjective'),
        ]

        for title, mode in history_topics:
            if mode == 'subjective':
                content_text = f'{title} - This historical event or figure played a crucial role in shaping human civilization and modern society. ' + \
                              'Understanding the context, causes, and consequences of this topic provides valuable insights into cultural, political, and economic developments. ' + \
                              'Studying history helps us learn from the past and make better decisions for the future.'
            else:
                content_text = f'{title} - Important historical facts and dates with context and significance.'

            additional_templates.append({
                'title': title,
                'content': content_text,
                'mode': mode
            })

        # Combine all templates
        all_templates = content_templates + additional_templates

        # Create 50 content items
        created_contents = []
        base_date = timezone.now() - timedelta(days=180)

        for i in range(min(50, len(all_templates))):
            template = all_templates[i]
            created_date = base_date + timedelta(days=i*3)  # Spread over 150 days

            content = Content.objects.create(
                author=user,
                title=template['title'],
                content=template['content'],
                review_mode=template['mode'],
                created_at=created_date,
                updated_at=created_date
            )
            created_contents.append(content)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(created_contents)} content items'))

        # Create ReviewSchedules with varying interval_index
        # PRO tier intervals: [1,3,7,14,30,60,120,180]
        from review.utils import get_review_intervals

        review_intervals = get_review_intervals(user)
        max_interval_index = len(review_intervals) - 1  # e.g., 7 for PRO

        review_schedules_created = 0
        review_histories_created = 0

        for i, content in enumerate(created_contents):
            # Vary interval_index (0 to max_interval_index) to simulate long-term learning
            interval_index = random.randint(0, max_interval_index)

            # Calculate next_review_date based on interval_index
            # Make sure it's after content creation
            days_since_creation = (timezone.now() - content.created_at).days

            # Some reviews are due today, some are overdue, some are future
            # But always after content creation
            random_offset = random.randint(-min(5, days_since_creation), 5)
            next_review = timezone.now() + timedelta(days=random_offset)

            # Get the auto-created review schedule (created by signal) and update it
            review_schedule = ReviewSchedule.objects.get(user=user, content=content)
            review_schedule.interval_index = interval_index
            review_schedule.next_review_date = next_review
            review_schedule.save()
            review_schedules_created += 1

            # Create realistic review history
            # More reviews for older content
            num_reviews = random.randint(interval_index + 1, interval_index + 5)

            for j in range(num_reviews):
                # Review dates going forwards from content creation
                review_date = content.created_at + timedelta(days=j*7)

                if review_date > timezone.now():
                    break

                # Realistic success rate: ~70-80%
                remembered = random.random() < 0.75
                result = 'remembered' if remembered else 'forgot'

                ReviewHistory.objects.create(
                    user=user,
                    content=content,
                    review_date=review_date,
                    result=result,
                    time_spent=random.randint(10, 120)  # seconds
                )
                review_histories_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {review_schedules_created} review schedules'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {review_histories_created} review history entries'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Subscription: PRO (active)')
        self.stdout.write(f'Content items: {len(created_contents)}')
        self.stdout.write(f'Review schedules: {review_schedules_created}')
        self.stdout.write(f'Review history: {review_histories_created}')
        self.stdout.write(self.style.SUCCESS('\nTest account ready for Playwright testing!'))
