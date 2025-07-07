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
        
        # Modify the persistent timestamp to test cache invalidation
        # We need to manipulate the persistent timestamp file, not just the cache file mtime
        timestamp_file = retriever._last_fetch_time_path
        if timestamp_file.exists():
            # Write an old timestamp to the persistent timestamp file
            yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
            old_timestamp_str = yesterday.isoformat().replace('+00:00', 'Z')
            with open(timestamp_file, 'w', encoding='utf-8') as f:
                f.write(old_timestamp_str)
            # Reload the timestamp from file
            retriever._load_last_fetch_time()
        
        # Check if cache is outdated - should be since we modified the persistent timestamp
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
    
    def test_persistent_timestamp_across_cli_invocations(self):
        """Test that persistent timestamp works across separate CLI invocations."""
        # First "CLI invocation" - create retriever and fetch registry
        retriever1 = RegistryRetriever(
            cache_ttl=300,  # 5 minutes TTL
            local_cache_dir=self.cache_dir,
            simulation_mode=False
        )
        
        # Get registry (should fetch from online)
        registry1 = retriever1.get_registry()
        self.assertIsNotNone(registry1)
        
        # Verify timestamp file was created
        self.assertTrue(retriever1._last_fetch_time_path.exists(), "Timestamp file should be created")
        
        # Get the timestamp from the first fetch
        first_fetch_time = retriever1._last_fetch_time
        self.assertGreater(first_fetch_time, 0, "First fetch time should be set")
        
        # Second "CLI invocation" - create new retriever with same cache directory
        retriever2 = RegistryRetriever(
            cache_ttl=300,  # 5 minutes TTL  
            local_cache_dir=self.cache_dir,
            simulation_mode=False
        )
        
        # Verify the timestamp was loaded from disk
        self.assertGreater(retriever2._last_fetch_time, 0, "Timestamp should be loaded from disk")
        
        # Get registry (should use cache since timestamp is recent)
        registry2 = retriever2.get_registry()
        self.assertIsNotNone(registry2)
        
        # Verify cache was used and not a new fetch (timestamp should be same or very close)
        time_diff = abs(retriever2._last_fetch_time - first_fetch_time)
        self.assertLess(time_diff, 2.0, "Should use cached registry, not fetch new one")
    
    def test_persistent_timestamp_edge_cases(self):
        """Test edge cases for persistent timestamp handling."""
        retriever = RegistryRetriever(
            cache_ttl=300,  # 5 minutes TTL
            local_cache_dir=self.cache_dir,
            simulation_mode=False
        )
        
        # Test 1: Corrupt timestamp file
        timestamp_file = retriever._last_fetch_time_path
        timestamp_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write corrupt data to timestamp file
        with open(timestamp_file, 'w', encoding='utf-8') as f:
            f.write("invalid_timestamp_data")
        
        # Should handle gracefully and treat as no timestamp
        retriever._load_last_fetch_time()
        self.assertEqual(retriever._last_fetch_time, 0, "Corrupt timestamp should be treated as no timestamp")
        
        # Test 2: Future timestamp (clock skew scenario)
        future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        future_timestamp_str = future_time.isoformat().replace('+00:00', 'Z')
        with open(timestamp_file, 'w', encoding='utf-8') as f:
            f.write(future_timestamp_str)
        
        retriever._load_last_fetch_time()
        # Should handle future timestamps gracefully (treat as valid but check TTL normally)
        self.assertGreater(retriever._last_fetch_time, 0, "Future timestamp should be loaded")
        
        # Test 3: Empty timestamp file
        with open(timestamp_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        retriever._load_last_fetch_time()
        self.assertEqual(retriever._last_fetch_time, 0, "Empty timestamp file should be treated as no timestamp")
        
        # Test 4: Missing timestamp file
        timestamp_file.unlink()
        retriever._load_last_fetch_time()
        self.assertEqual(retriever._last_fetch_time, 0, "Missing timestamp file should be treated as no timestamp")

if __name__ == "__main__":
    unittest.main()
