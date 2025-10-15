import java.nio.file.*;
import java.nio.file.StandardOpenOption;

/**
 * Test F9 ABEND Scenario
 * This program simulates F9 key press and triggers CEE3204S ABEND
 */
public class TestF9Abend {
    
    public static void main(String[] args) {
        System.out.println("*** F9 ABEND TEST SCENARIO ***");
        System.out.println("Simulating F9 key press that causes ABEND");
        
        try {
            // Simulate F9 key press detection
            String keyPressed = "F9";
            System.out.println("[TEST] F9 key detected: " + keyPressed);
            
            // Trigger ABEND scenario
            triggerF9Abend();
            
        } catch (Exception e) {
            System.err.println("[ERROR] Test failed: " + e.getMessage());
            e.printStackTrace();
            System.exit(999);
        }
    }
    
    private static void triggerF9Abend() {
        System.err.println("[ABEND] *** CRITICAL ERROR - CEE3204S ABEND TRIGGERED ***");
        System.err.println("[ABEND] ABEND CODE: CEE3204S");
        System.err.println("[ABEND] DESCRIPTION: The system detected a protection exception (System Completion Code=0C4)");
        System.err.println("[ABEND] CAUSE: F9 key pressed - unsupported function key access");
        System.err.println("[ABEND] LOCATION: TestF9Abend.triggerF9Abend()");
        System.err.println("[ABEND] TIMESTAMP: " + new java.util.Date());
        System.err.println("[ABEND] SCENARIO: DevOps Auto-Fix Testing - F9 Key ABEND");
        
        // Log ABEND to file for Zabbix monitoring
        logAbendToFile();
        
        // Create Zabbix trigger file
        createZabbixTriggerFile();
        
        // Display detailed error information
        System.err.println("[ABEND] *** SYSTEM DETAILS ***");
        System.err.println("[ABEND] SEVERITY: CRITICAL");
        System.err.println("[ABEND] IMPACT: System halt - User session terminated");
        System.err.println("[ABEND] ACTION_REQUIRED: Automatic remediation via CI/CD pipeline");
        System.err.println("[ABEND] EXPECTED_FIX: Deploy fixed MAIN001.class with proper F9 handling");
        System.err.println("[ABEND] MONITORING_TRIGGER: Zabbix should detect this ABEND and trigger auto-fix");
        
        System.err.println("[ABEND] *** SYSTEM DUMP INITIATED ***");
        System.err.println("[ABEND] *** PROGRAM TERMINATED ABNORMALLY ***");
        System.err.println("[ABEND] *** ZABBIX MONITORING SHOULD ACTIVATE AUTO-FIX PIPELINE ***");
        
        // Force abnormal termination with CEE3204S exit code
        System.exit(204); // Exit with CEE3204S code (204 = protection exception)
    }
    
    private static void logAbendToFile() {
        try {
            String logFile = "/home/aspuser/app/logs/abend.log";
            String timestamp = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new java.util.Date());
            
            String logEntry = String.format(
                "[%s] ABEND CEE3204S in TestF9Abend.triggerF9Abend(): F9 key pressed - Protection exception in function key handler (Terminal: system, Session: test_session)%n",
                timestamp
            );
            
            // Ensure log directory exists
            java.io.File logDir = new java.io.File("/home/aspuser/app/logs");
            if (!logDir.exists()) {
                logDir.mkdirs();
            }
            
            // Append to log file
            Files.write(
                Paths.get(logFile), 
                logEntry.getBytes(), 
                StandardOpenOption.CREATE, 
                StandardOpenOption.APPEND
            );
            
            System.err.println("[ABEND] ABEND logged to: " + logFile);
            
        } catch (Exception e) {
            System.err.println("[ABEND] Failed to log ABEND: " + e.getMessage());
        }
    }
    
    private static void createZabbixTriggerFile() {
        try {
            String triggerFile = "/home/aspuser/app/logs/zabbix_trigger.log";
            String timestamp = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new java.util.Date());
            
            String triggerEntry = String.format(
                "[%s] ZABBIX_TRIGGER ABEND=CEE3204S SCENARIO=F9_KEY_ABEND PROGRAM=TestF9Abend TERMINAL=system SESSION=test_session%n",
                timestamp
            );
            
            // Ensure log directory exists
            java.io.File logDir = new java.io.File("/home/aspuser/app/logs");
            if (!logDir.exists()) {
                logDir.mkdirs();
            }
            
            // Write trigger file
            Files.write(
                Paths.get(triggerFile), 
                triggerEntry.getBytes(), 
                StandardOpenOption.CREATE, 
                StandardOpenOption.APPEND
            );
            
            System.err.println("[ABEND] Zabbix trigger file created: " + triggerFile);
            System.err.println("[ABEND] Trigger content: " + triggerEntry.trim());
            
        } catch (Exception e) {
            System.err.println("[ABEND] Failed to create Zabbix trigger file: " + e.getMessage());
        }
    }
}