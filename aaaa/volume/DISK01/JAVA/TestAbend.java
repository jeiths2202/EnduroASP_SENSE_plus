import java.io.*;
import java.nio.file.*;
import java.nio.file.StandardOpenOption;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Test ABEND simulation for Zabbix monitoring verification
 */
public class TestAbend {
    
    public static void main(String[] args) {
        System.out.println("=== ABEND Test Simulation ===");
        System.out.println("Simulating F3 key ABEND for monitoring test");
        
        try {
            // Simulate F3 key ABEND
            triggerAbendOnF3();
        } catch (Exception e) {
            System.err.println("Test failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Simulate F3 key ABEND for testing
     */
    private static void triggerAbendOnF3() {
        System.err.println("[MAIN001] *** CRITICAL ERROR - ABEND TRIGGERED BY F3 KEY ***");
        System.err.println("[MAIN001] ABEND CODE: CEE3204S");
        System.err.println("[MAIN001] DESCRIPTION: The system detected a protection exception (System Completion Code=0C4)");
        System.err.println("[MAIN001] LOCATION: MAIN001.handleF3Key() at line 1170");
        System.err.println("[MAIN001] TIMESTAMP: " + new Date());
        System.err.println("[MAIN001] TERMINAL: webui");
        System.err.println("[MAIN001] SESSION: test_session_f3_abend");
        
        // Log ABEND to file for Zabbix monitoring
        logAbendToFile("CEE3204S", "Protection exception on F3 key press", "MAIN001.handleF3Key()");
        
        System.err.println("[MAIN001] *** SYSTEM DUMP INITIATED ***");
        System.err.println("[MAIN001] *** PROGRAM TERMINATED ABNORMALLY ***");
        
        // Force abnormal termination
        System.exit(9); // Exit with ABEND code
    }
    
    /**
     * Log ABEND information to file for Zabbix monitoring
     */
    private static void logAbendToFile(String abendCode, String description, String location) {
        try {
            String logFile = "/home/aspuser/app/logs/abend.log";
            String timestamp = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date());
            
            String logEntry = String.format(
                "[%s] ABEND %s in %s: %s (Terminal: webui, Session: test_session_f3_abend)%n",
                timestamp, abendCode, location, description
            );
            
            // Ensure log directory exists
            File logDir = new File("/home/aspuser/app/logs");
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
            
            System.err.println("[MAIN001] ABEND logged to: " + logFile);
            
        } catch (Exception e) {
            System.err.println("[MAIN001] Failed to log ABEND: " + e.getMessage());
        }
    }
}