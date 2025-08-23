import java.lang.reflect.Method;

/**
 * ABEND Test Trigger for CI/CD Workflow Testing
 * This program simulates F3 key press to trigger ABEND for monitoring
 */
public class trigger_abend_test {
    
    public static void main(String[] args) {
        System.out.println("===============================================");
        System.out.println("    ABEND CI/CD Workflow Test Trigger");
        System.out.println("===============================================");
        System.out.println("Current time: " + new java.util.Date());
        System.out.println("Testing: F3 key ABEND -> Zabbix -> DevOps Fix");
        System.out.println("");
        
        try {
            // Load MAIN001 class
            System.out.println("[INFO] Loading MAIN001 class...");
            Class<?> main001Class = Class.forName("MAIN001");
            
            // Create instance
            System.out.println("[INFO] Creating MAIN001 instance...");
            Object instance = main001Class.getDeclaredConstructor().newInstance();
            
            // Get handleF3Key method
            System.out.println("[INFO] Accessing handleF3Key method...");
            Method handleF3Method = main001Class.getDeclaredMethod("handleF3Key");
            handleF3Method.setAccessible(true);
            
            System.out.println("");
            System.out.println("[TRIGGER] Simulating F3 key press...");
            System.out.println("[TRIGGER] This should trigger CEE3204S ABEND");
            System.out.println("[TRIGGER] Zabbix should detect this ABEND");
            System.out.println("[TRIGGER] DevOps pipeline should start auto-fix");
            System.out.println("");
            
            // Trigger F3 key - This should cause ABEND
            handleF3Method.invoke(instance);
            
            System.out.println("[UNEXPECTED] F3 method completed without ABEND");
            
        } catch (Exception e) {
            System.out.println("");
            System.out.println("[SUCCESS] ABEND triggered as expected!");
            System.out.println("[SUCCESS] Exception: " + e.getClass().getSimpleName());
            System.out.println("[SUCCESS] Message: " + e.getMessage());
            
            if (e.getCause() != null) {
                System.out.println("[SUCCESS] Root cause: " + e.getCause().getMessage());
            }
            
            System.out.println("");
            System.out.println("[NEXT] Zabbix should detect this ABEND");
            System.out.println("[NEXT] DevOps auto-fix pipeline should activate");
            System.out.println("[NEXT] Check CI/CD Workflow Visualizer UI for updates");
        }
        
        System.out.println("");
        System.out.println("ABEND test trigger completed at: " + new java.util.Date());
        System.out.println("===============================================");
    }
}