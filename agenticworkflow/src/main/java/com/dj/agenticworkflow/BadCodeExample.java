package com.dj.agenticworkflow;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class BadCodeExample {

    private static String password = "hardcoded-password"; // security issue

    public void processData() {
        // TODO: optimize this later

        System.out.println("Starting process");

        List<String> list = new ArrayList<>();

        for (int i = 0; i < 10000; i++) {
            list.add("Item " + i); // inefficient if not needed
        }

        for (int i = 0; i < list.size(); i++) {
            System.out.println(list.get(i)); // heavy console logging
        }

        try {
            riskyOperation();
        } catch (Exception e) {
            // empty catch block
        }

        try {
            int x = 10 / 0;
        } catch (Exception e) {
            e.printStackTrace(); // bad logging
        }
    }

    private void riskyOperation() throws Exception {
        throw new Exception("Failure");
    }

    public void sqlInjectionExample(String userInput) {
        try {
            Connection conn = DriverManager.getConnection("jdbc:mysql://localhost/test", "root", password);
            Statement stmt = conn.createStatement();

            // SQL Injection vulnerability
            String query = "SELECT * FROM users WHERE name = '" + userInput + "'";
            stmt.executeQuery(query);

        } catch (Exception e) {
            System.out.println("Error"); // bad practice
        }
    }

    public void nullPointerExample() {
        String value = null;
        System.out.println(value.length()); // NPE risk
    }

    public void badThreadUsage() {
        new Thread(() -> {
            System.out.println("Running thread manually"); // bad practice
        }).start();
    }

    public void inefficientLoop() {
        List<Integer> numbers = List.of(1,2,3,4,5);

        for (int i = 0; i < numbers.size(); i++) {
            for (int j = 0; j < numbers.size(); j++) {
                System.out.println(numbers.get(i) + numbers.get(j)); // unnecessary nested loop
            }
        }
    }

    public void magicNumbers() {
        int result = 42 * 17 + 99; // magic numbers
        System.out.println(result);
    }
}
