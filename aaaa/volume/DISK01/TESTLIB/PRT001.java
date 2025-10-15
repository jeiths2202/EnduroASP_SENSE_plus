import java.io.*;
import java.nio.file.*;
import java.nio.charset.Charset;

public class PRT001 {
    public static void main(String[] args) {
        // Redirect System.out to System.err to ensure output is captured
        System.setOut(System.err);
        
        // Sleep for 5 seconds at start
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        String empFile = null;
        byte[] allBytes = null;
        
        // First, try to read override mappings from dslock_java_runtime
        try {
            Path overrideMappingsPath = Paths.get("/tmp/dslock_java_runtime/override_mappings.json");
            // System.err.println("DEBUG: Checking override file: " + overrideMappingsPath);
            // System.err.println("DEBUG: File exists: " + Files.exists(overrideMappingsPath));
            
            if (Files.exists(overrideMappingsPath)) {
                String jsonContent = new String(Files.readAllBytes(overrideMappingsPath));
                // System.err.println("DEBUG: JSON content: " + jsonContent.substring(0, Math.min(100, jsonContent.length())) + "...");
                
                // Simple JSON parsing to find EMP-FILE resolved_path
                if (jsonContent.contains("\"EMP-FILE\"")) {
                    int empFileIndex = jsonContent.indexOf("\"EMP-FILE\"");
                    int resolvedPathIndex = jsonContent.indexOf("\"resolved_path\"", empFileIndex);
                    
                    if (resolvedPathIndex > 0) {
                        int colonIndex = jsonContent.indexOf(":", resolvedPathIndex);
                        int quoteStart = jsonContent.indexOf("\"", colonIndex) + 1;
                        int quoteEnd = jsonContent.indexOf("\"", quoteStart);
                        
                        if (quoteStart > 0 && quoteEnd > quoteStart) {
                            empFile = jsonContent.substring(quoteStart, quoteEnd);
                            // System.err.println("DEBUG: Found EMP-FILE override: " + empFile);
                        }
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("Warning: Could not read override mappings: " + e.getMessage());
        }
        
        // Fallback to environment variable or default
        if (empFile == null) {
            empFile = System.getenv("EMP_FILE");
            if (empFile == null) {
                empFile = "volume/DISK01/TESTLIB/EMPLOYEE.FB";
            }
        }
        
        try {
            Path filePath = Paths.get(empFile);
            if (!Files.exists(filePath)) {
                filePath = Paths.get("/home/aspuser/app/" + empFile);
            }
            
            if (!Files.exists(filePath)) {
                System.err.println("Error: File not found: " + empFile);
                System.exit(1);
            }
            
            allBytes = Files.readAllBytes(filePath);
            
            int recordLength = 80;
            int recordCount = allBytes.length / recordLength;
            
            // System.err.println("DEBUG: Found " + recordCount + " records to process");
            // System.err.flush();
            
            for (int i = 0; i < recordCount; i++) {
                byte[] record = new byte[recordLength];
                System.arraycopy(allBytes, i * recordLength, record, 0, recordLength);
                
                String recordStr = new String(record, Charset.forName("Shift_JIS"));
                
                System.out.println(recordStr);
                System.out.flush();
            }
            
            // System.err.println("DEBUG: Finished processing all records");
            // System.err.flush();
            
        } catch (IOException e) {
            System.err.println("Error reading file: " + e.getMessage());
            System.exit(1);
        }
        
        // Also write to a debug file for troubleshooting
        try {
            Path debugFile = Paths.get("/tmp/prt001_debug.log");
            String debugInfo = "PRT001 executed successfully at " + new java.util.Date() + "\n";
            debugInfo += "EMP-FILE resolved to: " + empFile + "\n";
            debugInfo += "Records processed: " + (allBytes != null ? allBytes.length / 80 : 0) + "\n";
            java.nio.file.Files.write(debugFile, debugInfo.getBytes(), java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
        } catch (Exception debugEx) {
            // Ignore debug file errors
        }
    }
}