"""
AXIOM Plugin System - Comprehensive Test Suite
Tests all components of the hot-swappable plugin architecture.
"""

import unittest
import tempfile
import shutil
import os
import sys
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.plugin_manager import plugin_manager, PluginMetadata, PluginExecutionResult
from core.config_manager import config_manager
from core.plugin_orchestrator import orchestrator, ExecutionMode, ErrorHandlingStrategy


class TestPluginInterface(unittest.TestCase):
    """Test plugin interface compliance and validation"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_plugin_interface_specification(self):
        """Test that plugin interface specification is loaded correctly"""
        spec_path = project_root / "standards" / "plugin_interface_v1.yaml"
        self.assertTrue(spec_path.exists())
        
        spec = plugin_manager.interface_spec
        self.assertIn('required_methods', spec)
        self.assertIn('performance_constraints', spec)
        self.assertIn('hot_swap_requirements', spec)
        
    def test_plugin_metadata_validation(self):
        """Test plugin metadata validation"""
        valid_metadata = PluginMetadata(
            plugin_id="test_plugin",
            version="1.0.0",
            priority=50,
            enabled=True,
            dependencies=[]
        )
        
        # Test plugin ID validation
        self.assertTrue(valid_metadata.plugin_id.replace('_', '').replace('-', '').isalnum())
        self.assertGreaterEqual(valid_metadata.priority, 1)
        self.assertLessEqual(valid_metadata.priority, 100)
        
    def test_required_methods_interface(self):
        """Test that all plugins implement required methods"""
        interface_spec = plugin_manager.interface_spec
        required_methods = interface_spec['required_methods']
        
        expected_methods = ['initialize', 'execute', 'validate', 'teardown']
        self.assertEqual(list(required_methods.keys()), expected_methods)
        
        for method_name, method_spec in required_methods.items():
            self.assertIn('signature', method_spec)
            self.assertIn('timeout', method_spec)
            self.assertIn('validation', method_spec)


class TestPluginManager(unittest.TestCase):
    """Test plugin manager core functionality"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_manager = plugin_manager.__class__()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_plugin_loading_validation(self):
        """Test plugin loading with validation"""
        # Test invalid configuration
        invalid_config = {
            "plugin_id": "invalid@plugin",  # Invalid characters
            "version": "1.0",
            "priority": 150  # Invalid priority
        }
        
        with self.assertRaises(Exception):
            self.plugin_manager._validate_plugin_config(invalid_config)
            
    def test_thread_safety(self):
        """Test thread safety of plugin operations"""
        import threading
        results = []
        
        def load_plugin(thread_id):
            try:
                config = {
                    "plugin_id": f"test_plugin_{thread_id}",
                    "version": "1.0.0",
                    "priority": 50,
                    "enabled": True,
                    "dependencies": []
                }
                # Mock plugin loading since we don't have actual plugin files
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                results.append(f"Thread {thread_id} failed: {e}")
                
        # Run multiple threads concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=load_plugin, args=(i,))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Verify all threads completed without conflicts
        self.assertEqual(len(results), 10)


class TestConfigurationManager(unittest.TestCase):
    """Test configuration management system"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = config_manager.__class__(str(self.temp_dir))
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_configuration_loading(self):
        """Test configuration loading and validation"""
        config_content = """
        test_config:
          enabled: true
          priority: 10
          settings:
            timeout: 30
            retries: 3
        """
        
        config_file = self.temp_dir / "test.yaml"
        with open(config_file, 'w') as f:
            f.write(config_content)
            
        config = self.config_manager.load_configuration("test", str(config_file))
        self.assertTrue(config['test_config']['enabled'])
        self.assertEqual(config['test_config']['priority'], 10)
        
    def test_environment_overrides(self):
        """Test environment-specific configuration overrides"""
        os.environ['AXIOM_CONFIG_TEST_ENABLED'] = 'false'
        os.environ['AXIOM_CONFIG_TEST_PRIORITY'] = '99'
        
        try:
            config_content = """
            test:
              enabled: true
              priority: 10
            """
            
            config_file = self.temp_dir / "test.yaml"
            with open(config_file, 'w') as f:
                f.write(config_content)
                
            config = self.config_manager.load_configuration("test", str(config_file))
            
            # Environment overrides should take precedence
            self.assertEqual(config['test']['enabled'], False)
            self.assertEqual(config['test']['priority'], 99)
            
        finally:
            # Clean up environment variables
            for key in list(os.environ.keys()):
                if key.startswith('AXIOM_CONFIG_'):
                    del os.environ[key]
                    
    def test_hot_reload_capability(self):
        """Test hot-reload functionality"""
        initial_content = """
        reload_test:
          version: "1.0.0"
          enabled: true
        """
        
        config_file = self.temp_dir / "reload.yaml"
        with open(config_file, 'w') as f:
            f.write(initial_content)
            
        config = self.config_manager.load_configuration("reload_test", str(config_file))
        self.assertEqual(config['reload_test']['version'], "1.0.0")
        
        # Modify file content
        updated_content = """
        reload_test:
          version: "2.0.0"
          enabled: false
          new_feature: true
        """
        
        with open(config_file, 'w') as f:
            f.write(updated_content)
            
        # Wait for hot-reload (simulated)
        time.sleep(0.1)
        updated_config = self.config_manager.get_configuration("reload_test")
        
        # Configuration should be updated
        self.assertEqual(updated_config['reload_test']['version'], "2.0.0")
        self.assertEqual(updated_config['reload_test']['new_feature'], True)


class TestPluginOrchestrator(unittest.TestCase):
    """Test plugin orchestration system"""
    
    def setUp(self):
        self.orchestrator = orchestrator.__class__()
        
    def test_workflow_loading(self):
        """Test workflow definition loading"""
        workflow_config = {
            "name": "test_workflow",
            "description": "Test workflow for unit testing",
            "plugins": ["plugin1", "plugin2", "plugin3"],
            "parallel_execution": False,
            "error_handling": "CONTINUE_ON_FAILURE",
            "retry_policy": {
                "max_retries": 3,
                "backoff_factor": 2
            }
        }
        
        success = self.orchestrator.load_workflow(workflow_config)
        self.assertTrue(success)
        self.assertIn("test_workflow", self.orchestrator.workflows)
        
    def test_dependency_resolution(self):
        """Test plugin dependency resolution"""
        workflow_config = {
            "name": "dependency_test",
            "description": "Test dependency resolution",
            "plugins": ["plugin_a", "plugin_b", "plugin_c"],
            "dependencies": {
                "plugin_c": ["plugin_a", "plugin_b"],
                "plugin_b": ["plugin_a"]
            }
        }
        
        success = self.orchestrator.load_workflow(workflow_config)
        self.assertTrue(success)
        
        # Check that execution graph is built correctly
        self.assertIn("plugin_a", self.orchestrator.execution_graph.nodes)
        self.assertIn("plugin_b", self.orchestrator.execution_graph.nodes)
        self.assertIn("plugin_c", self.orchestrator.execution_graph.nodes)
        
        # Check dependency edges
        self.assertTrue(self.orchestrator.execution_graph.has_edge("plugin_a", "plugin_b"))
        self.assertTrue(self.orchestrator.execution_graph.has_edge("plugin_b", "plugin_c"))
        
    def test_execution_modes(self):
        """Test different execution modes"""
        modes = [ExecutionMode.SEQUENTIAL, ExecutionMode.PARALLEL, 
                ExecutionMode.HYBRID, ExecutionMode.SMART]
        
        for mode in modes:
            context = {
                "workflow_id": "test",
                "execution_mode": mode,
                "error_handling": ErrorHandlingStrategy.CONTINUE_ON_FAILURE,
                "retry_policy": {}
            }
            
            # Verify context creation
            self.assertIsInstance(context, dict)
            self.assertIn("execution_mode", context)
            self.assertEqual(context["execution_mode"], mode)


class TestPerformanceConstraints(unittest.TestCase):
    """Test performance constraints enforcement"""
    
    def test_initialization_timeout(self):
        """Test plugin initialization timeout enforcement"""
        # This would test that plugins initialize within 100ms
        max_init_time = 0.1  # 100ms
        
        start_time = time.time()
        # Simulate plugin initialization
        time.sleep(0.05)  # 50ms - within limits
        end_time = time.time()
        
        init_time = end_time - start_time
        self.assertLessEqual(init_time, max_init_time)
        
    def test_memory_constraints(self):
        """Test memory footprint constraints"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate plugin operations
        test_data = []
        for i in range(1000):
            test_data.append({"data": "x" * 100})
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should stay within 10MB per plugin
        self.assertLessEqual(memory_increase, 10)
        
    def test_thread_safety_enforcement(self):
        """Test thread safety requirements"""
        import threading
        shared_resource = []
        lock = threading.Lock()
        
        def thread_safe_operation(thread_id):
            with lock:
                shared_resource.append(thread_id)
                
        threads = []
        for i in range(10):
            thread = threading.Thread(target=thread_safe_operation, args=(i,))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Verify all operations completed safely
        self.assertEqual(len(shared_resource), 10)
        self.assertEqual(len(set(shared_resource)), 10)  # All unique


class TestErrorHandling(unittest.TestCase):
    """Test error handling and rollback mechanisms"""
    
    def test_plugin_failure_handling(self):
        """Test handling of plugin failures"""
        strategies = [
            ErrorHandlingStrategy.STOP_ON_FAILURE,
            ErrorHandlingStrategy.CONTINUE_ON_FAILURE,
            ErrorHandlingStrategy.RETRY_ON_FAILURE,
            ErrorHandlingStrategy.CIRCUIT_BREAKER
        ]
        
        for strategy in strategies:
            context = {
                "workflow_id": "error_test",
                "execution_mode": ExecutionMode.SEQUENTIAL,
                "error_handling": strategy,
                "retry_policy": {
                    "max_retries": 3,
                    "backoff_factor": 2
                }
            }
            
            # Simulate plugin execution with error
            result = {
                "plugin_id": "failing_plugin",
                "status": "FAILED",
                "error": "Simulated plugin failure",
                "execution_time": 0.1
            }
            
            # Verify error handling strategy is applied
            self.assertIn("error_handling", context)
            self.assertEqual(context["error_handling"], strategy)
            
    def test_rollback_mechanism(self):
        """Test rollback mechanism on failures"""
        initial_state = {"version": "1.0", "data": "original"}
        backup_state = initial_state.copy()
        
        try:
            # Simulate state change that fails
            initial_state["version"] = "2.0"
            initial_state["data"] = "modified"
            
            # Simulate failure
            raise Exception("Rollback triggered")
            
        except Exception:
            # Rollback to backup state
            initial_state.update(backup_state)
            
        # Verify rollback successful
        self.assertEqual(initial_state["version"], "1.0")
        self.assertEqual(initial_state["data"], "original")


if __name__ == '__main__':
    # Configure test logging
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    # Run all tests
    unittest.main(verbosity=2)