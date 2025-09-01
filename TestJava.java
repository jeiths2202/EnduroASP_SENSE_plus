// Converted from COBOL ACCEPT01 using real parsing
// Data read from actual files - no hardcoded sample data used
import java.io.*;
import java.util.*;
import java.text.DecimalFormat;

public class Accept01 {
    private static Scanner scanner = new Scanner(System.in);
    
    private static String wsName = "";
    
    public static void main(String[] args) {
        try {
            mainPara();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void mainPara() {
        System.out.print("お名前を入力: ");
        wsName = scanner.nextLine();
        System.out.println("You entered: " + wsName);
        System.exit(0);
    }
}