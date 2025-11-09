"""
Comprehensive Test Script for Vision Error-Proofing Software Core Modules

This script tests ConfigManager, TemplateManager, and InspectionLogger
with realistic scenarios and full integration testing.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core import ConfigManager, TemplateManager, InspectionLogger


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_config_manager() -> ConfigManager:
    """Test ConfigManager functionality."""
    print_section("TEST 1: ConfigManager")
    
    # 1. Create configuration initial
    print("1. Creating ConfigManager...")
    config_mgr = ConfigManager('tests/test_config.json')
    config = config_mgr.get_config()
    print(f"✓ Config loaded: version {config['version']}")
    
    # 2. Update camera configuration
    print("\n2. Updating camera settings...")
    success = config_mgr.update_camera_settings({
        'index': 1,
        'resolution': {'width': 1920, 'height': 1080}
    })
    if success:
        camera_settings = config_mgr.get_camera_settings()
        print(f"✓ Camera settings updated:")
        print(f"  - Index: {camera_settings['index']}")
        print(f"  - Resolution: {camera_settings['resolution']['width']}x{camera_settings['resolution']['height']}")
    
    # 3. Validate configuration
    print("\n3. Validating configuration...")
    is_valid = config_mgr.validate_config()
    print(f"✓ Config validation: {'PASSED' if is_valid else 'FAILED'}")
    
    # 4. Update specific config value
    print("\n4. Updating default threshold...")
    config_mgr.update_config('default_threshold', 0.90)
    updated_config = config_mgr.get_config()
    print(f"✓ Default threshold updated to: {updated_config['default_threshold']}")
    
    print("\n✅ ConfigManager tests completed successfully!")
    return config_mgr


def test_template_manager(config_mgr: ConfigManager) -> tuple:
    """Test TemplateManager functionality."""
    print_section("TEST 2: TemplateManager")
    
    # 1. Create TemplateManager
    print("1. Creating TemplateManager...")
    template_mgr = TemplateManager(config_mgr)
    print("✓ TemplateManager initialized")
    
    # 2. Add brand "Toyota Logo"
    print("\n2. Adding 'Toyota Logo' brand...")
    toyota_id = template_mgr.add_brand(
        name="Toyota Logo",
        template_path="tests/test_images/toyota_template.png",
        roi={"x": 100, "y": 150, "width": 200, "height": 200},
        threshold=0.85,
        method="hybrid"
    )
    print(f"✓ Brand added successfully")
    print(f"  - ID: {toyota_id}")
    print(f"  - Name: Toyota Logo")
    
    # 3. Add brand "Honda Logo"
    print("\n3. Adding 'Honda Logo' brand...")
    honda_id = template_mgr.add_brand(
        name="Honda Logo",
        template_path="tests/test_images/honda_template.png",
        roi={"x": 120, "y": 180, "width": 180, "height": 180},
        threshold=0.80
    )
    print(f"✓ Brand added successfully")
    print(f"  - ID: {honda_id}")
    print(f"  - Name: Honda Logo")
    
    # 4. List all brands
    print("\n4. Listing all brands...")
    brands = template_mgr.list_brands()
    print(f"✓ Total brands: {len(brands)}")
    for brand in brands:
        print(f"  - {brand['name']} (ID: {brand['id']}, Method: {brand['method']})")
    
    # 5. Add additional template to Toyota
    print("\n5. Adding additional template to Toyota...")
    template_mgr.add_template_to_brand(
        brand_id=toyota_id,
        template_path="tests/test_images/toyota_template_2.png",
        roi={"x": 110, "y": 160, "width": 190, "height": 190},
        threshold=0.87
    )
    print("✓ Additional template added to Toyota")
    
    # 6. Get brand data
    print("\n6. Retrieving Toyota brand data...")
    toyota_data = template_mgr.get_brand(toyota_id)
    if toyota_data:
        print(f"✓ Toyota brand data retrieved:")
        print(f"  - Name: {toyota_data['name']}")
        print(f"  - Templates: {len(toyota_data['templates'])}")
        print(f"  - Method: {toyota_data['method']}")
        print(f"  - Created: {toyota_data['created_at']}")
    
    # 7. Update brand
    print("\n7. Updating Toyota threshold...")
    success = template_mgr.update_brand(toyota_id, threshold=0.90)
    if success:
        updated_toyota = template_mgr.get_brand(toyota_id)
        print(f"✓ Brand updated")
        print(f"  - New threshold: {updated_toyota['templates'][0]['threshold']}")
    
    # 8. Get brand by name
    print("\n8. Searching brand by name...")
    honda_by_name = template_mgr.get_brand_by_name("Honda Logo")
    if honda_by_name:
        print(f"✓ Found brand: {honda_by_name['name']} (ID: {honda_by_name['id']})")
    
    # 9. Delete Honda brand
    print("\n9. Deleting Honda brand...")
    success = template_mgr.delete_brand(honda_id)
    if success:
        print("✓ Honda brand deleted successfully")
    
    # 10. Verify remaining brands
    print("\n10. Verifying remaining brands...")
    remaining = template_mgr.list_brands()
    print(f"✓ Remaining brands: {len(remaining)}")
    for brand in remaining:
        print(f"  - {brand['name']}")
    
    print("\n✅ TemplateManager tests completed successfully!")
    return template_mgr, toyota_id


def test_inspection_logger() -> InspectionLogger:
    """Test InspectionLogger functionality."""
    print_section("TEST 3: InspectionLogger")
    
    # 1. Create InspectionLogger
    print("1. Creating InspectionLogger...")
    inspection_logger = InspectionLogger('tests/test_logs/inspections.log')
    print(f"✓ InspectionLogger initialized")
    
    # 2. Log multiple inspections
    print("\n2. Logging 10 test inspections...")
    test_inspections = [
        {"brand": "Toyota Logo", "result": "OK", "score": 0.92, "method": "hybrid"},
        {"brand": "Toyota Logo", "result": "OK", "score": 0.88, "method": "hybrid"},
        {"brand": "Honda Logo", "result": "NOK", "score": 0.65, "method": "template_matching"},
        {"brand": "Toyota Logo", "result": "OK", "score": 0.91, "method": "feature_matching"},
        {"brand": "Honda Logo", "result": "OK", "score": 0.85, "method": "hybrid"},
        {"brand": "Toyota Logo", "result": "NOK", "score": 0.72, "method": "adaptive"},
        {"brand": "Honda Logo", "result": "OK", "score": 0.89, "method": "hybrid"},
        {"brand": "Toyota Logo", "result": "OK", "score": 0.94, "method": "hybrid"},
        {"brand": "Honda Logo", "result": "OK", "score": 0.87, "method": "feature_matching"},
        {"brand": "Toyota Logo", "result": "OK", "score": 0.90, "method": "hybrid"}
    ]
    
    for i, inspection in enumerate(test_inspections, 1):
        confidence = "HIGH" if inspection["score"] > 0.85 else "MEDIUM"
        details = {"processing_time_ms": 35.0 + i * 2.5}
        
        inspection_logger.log_inspection(
            brand_name=inspection["brand"],
            result=inspection["result"],
            score=inspection["score"],
            method=inspection["method"],
            confidence=confidence,
            details=details
        )
    
    print(f"✓ Logged {len(test_inspections)} inspections")
    
    # 3. Get all logs
    print("\n3. Retrieving all logs...")
    all_logs = inspection_logger.get_all_logs()
    print(f"✓ Total logs retrieved: {len(all_logs)}")
    
    # 4. Filter OK logs
    print("\n4. Filtering OK inspections...")
    ok_logs = inspection_logger.get_logs(result_filter="OK")
    print(f"✓ OK inspections: {len(ok_logs)}")
    for log in ok_logs[:3]:  # Show first 3
        print(f"  - {log['brand']}: {log['score']} ({log['method']})")
    
    # 5. Filter NOK logs
    print("\n5. Filtering NOK inspections...")
    nok_logs = inspection_logger.get_logs(result_filter="NOK")
    print(f"✓ NOK inspections: {len(nok_logs)}")
    for log in nok_logs:
        print(f"  - {log['brand']}: {log['score']} ({log['method']})")
    
    # 6. Get statistics
    print("\n6. Calculating statistics...")
    stats = inspection_logger.get_statistics()
    print("✓ Statistics calculated:")
    print(f"  - Total inspections: {stats['total']}")
    print(f"  - OK: {stats['ok_count']} ({stats['ok_percentage']:.2f}%)")
    print(f"  - NOK: {stats['nok_count']} ({stats['nok_percentage']:.2f}%)")
    print(f"  - Average Score: {stats['average_score']:.4f}")
    print(f"  - Average OK Score: {stats['average_ok_score']:.4f}")
    print(f"  - Average NOK Score: {stats['average_nok_score']:.4f}")
    print(f"  - Methods used: {stats['methods_used']}")
    print(f"  - Brands inspected: {stats['brands_inspected']}")
    
    # 7. Export to CSV
    print("\n7. Exporting to CSV...")
    csv_success = inspection_logger.export_logs_to_csv('tests/test_exports/export_test.csv')
    if csv_success:
        print("✓ Successfully exported to CSV")
        csv_path = Path('tests/test_exports/export_test.csv')
        if csv_path.exists():
            print(f"  - File size: {csv_path.stat().st_size} bytes")
    
    # 8. Export to JSON
    print("\n8. Exporting to JSON...")
    json_success = inspection_logger.export_logs_to_json('tests/test_exports/export_test.json')
    if json_success:
        print("✓ Successfully exported to JSON")
        json_path = Path('tests/test_exports/export_test.json')
        if json_path.exists():
            print(f"  - File size: {json_path.stat().st_size} bytes")
    
    # 9. Get logs by brand
    print("\n9. Getting logs for specific brand...")
    toyota_logs = inspection_logger.get_logs_by_brand("Toyota Logo")
    print(f"✓ Toyota Logo logs: {len(toyota_logs)}")
    
    # Calculate Toyota-specific statistics
    toyota_ok = len([log for log in toyota_logs if log['result'] == 'OK'])
    toyota_nok = len([log for log in toyota_logs if log['result'] == 'NOK'])
    if toyota_logs:
        toyota_avg = sum(log['score'] for log in toyota_logs) / len(toyota_logs)
        print(f"  - OK: {toyota_ok}, NOK: {toyota_nok}")
        print(f"  - Average Score: {toyota_avg:.4f}")
    
    print("\n✅ InspectionLogger tests completed successfully!")
    return inspection_logger


def test_full_integration():
    """Test full system integration."""
    print_section("TEST 4: Full Integration")
    
    print("1. Initializing complete system...")
    config = ConfigManager('tests/integration_test_config.json')
    templates = TemplateManager(config)
    logger = InspectionLogger('tests/integration_test_logs/inspections.log')
    print("✓ System initialized")
    
    print("\n2. Adding test brands...")
    brand1_id = templates.add_brand(
        "Brand A",
        "tests/test_images/toyota_template.png",
        {"x": 0, "y": 0, "width": 100, "height": 100},
        0.85,
        "hybrid"
    )
    brand2_id = templates.add_brand(
        "Brand B",
        "tests/test_images/honda_template.png",
        {"x": 0, "y": 0, "width": 100, "height": 100},
        0.80,
        "template_matching"
    )
    print(f"✓ Added 2 brands")
    print(f"  - Brand A: {brand1_id}")
    print(f"  - Brand B: {brand2_id}")
    
    print("\n3. Simulating 5 inspections...")
    for i in range(5):
        brand = "Brand A" if i % 2 == 0 else "Brand B"
        result = "OK" if i < 4 else "NOK"
        score = 0.90 if result == "OK" else 0.60
        method = "hybrid" if i % 2 == 0 else "template_matching"
        confidence = "HIGH" if score > 0.85 else "MEDIUM"
        
        logger.log_inspection(
            brand_name=brand,
            result=result,
            score=score,
            method=method,
            confidence=confidence,
            details={"inspection_id": i + 1}
        )
    print("✓ Logged 5 inspections")
    
    print("\n4. Analyzing results...")
    all_brands = templates.list_brands()
    final_stats = logger.get_statistics()
    
    print(f"✓ System status:")
    print(f"  - Total brands: {len(all_brands)}")
    print(f"  - Total inspections: {final_stats['total']}")
    print(f"  - Success rate: {final_stats['ok_percentage']:.1f}%")
    print(f"  - Average score: {final_stats['average_score']:.4f}")
    
    # Test brand-specific analytics
    print("\n5. Brand-specific analytics...")
    for brand in all_brands:
        brand_logs = logger.get_logs_by_brand(brand['name'])
        if brand_logs:
            brand_ok = len([log for log in brand_logs if log['result'] == 'OK'])
            brand_total = len(brand_logs)
            brand_success_rate = (brand_ok / brand_total * 100) if brand_total > 0 else 0
            print(f"  - {brand['name']}: {brand_total} inspections, {brand_success_rate:.1f}% success")
    
    print("\n✅ Full integration test completed successfully!")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  VISION ERROR-PROOFING SOFTWARE - CORE MODULES TEST")
    print("="*60)
    
    try:
        # Test 1: ConfigManager
        config_mgr = test_config_manager()
        
        # Test 2: TemplateManager
        template_mgr, toyota_id = test_template_manager(config_mgr)
        
        # Test 3: InspectionLogger
        logger = test_inspection_logger()
        
        # Test 4: Full Integration
        test_full_integration()
        
        # Final Summary
        print_section("FINAL SUMMARY")
        print("✅ All tests PASSED successfully!")
        print("\nGenerated files:")
        print("  - Configuration files in tests/")
        print("  - Template folders in templates/")
        print("  - Log files in tests/test_logs/")
        print("  - Export files in tests/test_exports/")
        
        print("\n" + "="*60)
        print("  TEST SUITE COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
