from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.publications.models import Publication

from .models import PublicationTextMining, TextMiningRun
from .services import run_text_mining


class TextMiningServiceTests(TestCase):
    def test_run_text_mining_creates_run_and_results(self):
        user = get_user_model().objects.create(username="admin")
        publication = Publication.objects.create(
            title="Machine learning for agricultural economics",
            abstract="This paper studies machine learning models for agricultural forecasting and policy analysis.",
            authors="Research Team",
            keywords="machine learning, agriculture, policy",
        )

        run = run_text_mining(
            Publication.objects.filter(pk=publication.pk),
            initiated_by=user,
            title="Selected publications",
            source_fields=["title", "abstract"],
        )

        self.assertEqual(run.status, TextMiningRun.STATUS_COMPLETED)
        self.assertEqual(run.analyzed_count, 1)
        self.assertTrue(run.top_terms)
        self.assertEqual(run.source_fields, ["title", "abstract"])
        self.assertTrue(run.topic_summary)

        result = PublicationTextMining.objects.get(run=run, publication=publication)
        self.assertGreater(result.token_count, 0)
        self.assertIn("machine", result.generated_keywords)
        self.assertEqual(result.primary_topic, "Agriculture")
