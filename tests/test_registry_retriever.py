import sys
import unittest
import tempfile
import shutil
import logging
import json
import datetime
import os
from pathlib import Path

# Add parent directory to path for direct testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.registry_retriever import RegistryRetriever

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hatch.registry_tests")


class RegistryRetrieverTests(unittest.TestCase):
    """Tests for Registry Retriever functionality."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to the registry file (using the one in project data) - for fallback/reference only
        self.registry_path = Path(__file__).parent.parent.parent / "data" / "hatch_packages_registry.json"
        if not self.registry_path.exists():
            # Try alternate location
            self.registry_path = Path(__file__).parent.parent.parent / "Hatch-Registry" / "data" / "hatch_packages_registry.json"
        
        # We're testing online mode, but keep a local copy for comparison and backup
        self.local_registry_path = Path(self.temp_dir) / "hatch_packages_registry.json"
        if self.registry_path.exists():
            shutil.copy(self.registry_path, self.local_registry_path)
        
    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_registry_init(self):
        """Test initialization of registry retriever."""
        # Test initialization in online mode (primary test focus)
        online_retriever = RegistryRetriever(
            local_cache_dir=self.cache_dir,
            simulation_mode=False
        )
        
        # Verify URL format for online mode
        self.assertTrue(online_retriever.registry_url.startswith("https://"))
        self.assertTrue("github.com" in online_retriever.registry_url)
        
        # Verify cache path is set correctly
        self.assertEqual(
            online_retriever.registry_cache_path, 
            self.cache_dir / "registry" / "hatch_packages_registry.json"
        )
        
        # Also test initialization with local file in simulation mode (for reference)
        sim_retriever = RegistryRetriever(
            local_cache_dir=self.cache_dir,
            simulation_mode=True,
            local_registry_cache_path=self.local_registry_path
        )
        
        # Verify registry cache path is set correctly in simulation mode
        self.assertEqual(sim_retriever.registry_cache_path, self.local_registry_path)
        self.assertTrue(sim_retriever.registry_url.startswith("file://"))
    
    def test_registry_cache_management(self):
        """Test registry cache management."""
        # Initialize retriever with a short TTL in online mode
        retriever = RegistryRetriever(
            cache_ttl=5,  # 5 seconds TTL
            local_cache_dir=self.cache_dir
        )
        
        # Get registry data (first fetch from online)
        registry_data1 = retriever.get_registry()
        self.assertIsNotNone(registry_data1)
        
        # Verify in-memory cache works (should not read from disk)
        registry_data2 = retriever.get_registry()
        self.assertIs(registry_data1, registry_data2)  # Should be the same object in memory
        
        # Force refresh and verify it gets loaded again (potentially from online)
        registry_data3 = retriever.get_registry(force_refresh=True)
        self.assertIsNotNone(registry_data3)
        
        # Verify the cache file was created
        self.assertTrue(retriever.registry_cache_path.exists(), "Cache file was not created")
        
        # Modify the cache timestamp to test cache invalidation
        registry_cache_path = retriever.registry_cache_path
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        yesterday_timestamp = yesterday.timestamp()
        os.utime(registry_cache_path, (yesterday_timestamp, yesterday_timestamp))
          # Check if cache is outdated - should be since we modified the timestamp
        self.assertTrue(retriever.is_cache_outdated())
        
        # Force refresh and verify new data is loaded (should fetch from online)
        registry_data4 = retriever.get_registry(force_refresh=True)
        self.assertIsNotNone(registry_data4)
        self.assertIn("repositories", registry_data4)
        self.assertIn("last_updated", registry_data4)
    
    def test_online_mode(self):
        """Test registry retriever in online mode."""
        # Initialize in online mode
        retriever = RegistryRetriever(
            local_cache_dir=self.cache_dir,
            simulation_mode=False
        )
        
        # Get registry and verify it contains expected data
        registry = retriever.get_registry()
        self.assertIn("repositories", registry)
        self.assertIn("last_updated", registry)
        
        # Verify registry structure
        self.assertIsInstance(registry.get("repositories"), list)
        self.assertGreater(len(registry.get("repositories", [])), 0, "Registry should contain repositories")
        
        # Get registry again with force refresh (should fetch from online)
        registry2 = retriever.get_registry(force_refresh=True)
        self.assertIn("repositories", registry2)
          # Test error handling with an existing cache
        # First ensure we have a valid cache file
        self.assertTrue(retriever.registry_cache_path.exists(), "Cache file should exist after previous calls")
        
        # Create a new retriever with invalid URL but using the same cache
        bad_retriever = RegistryRetriever(
            local_cache_dir=self.cache_dir,
            simulation_mode=False
        )
        # Mock the URL to be invalid
        bad_retriever.registry_url = "https://nonexistent.example.com/registry.json"
        
        # First call should use the cache that was created by the earlier tests
        registry_data = bad_retriever.get_registry()
        self.assertIsNotNone(registry_data)
        
        # Verify an attempt to force refresh with invalid URL doesn't break the test
        try:
            bad_retriever.get_registry(force_refresh=True)
        except Exception:
            pass  # Expected to fail, that's OK


if __name__ == "__main__":
    unittest.main()
