"""
Created on 2024-10-24

@author: wf
"""

from genwiki.playground import Playground
from tests.gbasetest import GenealogyBasetest


class TestPlayground(GenealogyBasetest):
    """
    test playground generation
    """

    def setUp(self, debug=True, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)
        self.playground = Playground()

    def test_thumbnail_generation(self):
        """
        Test that the thumbnail URL is correctly generated from the original image URL
        with different sizes using subTest, and output the result for manual verification.
        """
        original_url = "https://upload.wikimedia.org/wikipedia/commons/b/b8/Aristaeus_Bosio_Louvre_LL51.jpg"
        test_sizes = [300, 131]

        for size in test_sizes:
            with self.subTest(size=size):
                thumbnail_url = self.playground.get_thumbnail_url(
                    original_url, size=size
                )
                # Debug output for manual verification
                if self.debug:
                    print(f"Generated thumbnail URL for size {size}: {thumbnail_url}")
                # Assert that the thumbnail URL contains the size
                self.assertIn(f"/{size}px-", thumbnail_url)
                self.assertTrue(
                    thumbnail_url.startswith(
                        "https://upload.wikimedia.org/wikipedia/commons/thumb/"
                    )
                )
