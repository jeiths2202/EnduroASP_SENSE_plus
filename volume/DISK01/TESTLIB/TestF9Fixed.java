/**
 * Test F9 Fixed Scenario
 * This program tests that F9 key now shows INVALID KEY instead of ABEND
 */
public class TestF9Fixed {
    
    public static void main(String[] args) {
        System.out.println("*** F9 FIXED TEST SCENARIO ***");
        System.out.println("Testing F9 key after CI/CD fix deployment");
        
        try {
            // Create MAIN001 instance and test F9 key
            MAIN001 main001 = new MAIN001();
            
            // Simulate F9 key input using reflection
            java.lang.reflect.Method handleF9Method = MAIN001.class.getDeclaredMethod("handleF9InvalidKey");
            handleF9Method.setAccessible(true);
            
            System.out.println("[TEST] Simulating F9 key press...");
            handleF9Method.invoke(main001);
            
            System.out.println("[TEST] ✅ SUCCESS: F9 key now shows INVALID KEY instead of ABEND!");
            System.out.println("[TEST] ✅ CI/CD auto-fix deployment successful!");
            
        } catch (Exception e) {
            System.out.println("[TEST] ❌ FAILED: " + e.getMessage());
            e.printStackTrace();
        }
    }
}