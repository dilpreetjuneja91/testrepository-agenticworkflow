package com.yourorg.test;

public class TestMe {

    public void doSomething() {
        // TODO: fix this logic later

        System.out.println("Starting process...");

        try {
            riskyOperation();
        } catch (Exception e) {
            // empty catch block (bad)
        }

        System.out.println("Process completed");
    }

    private void riskyOperation() throws Exception {
        if (true) {
            throw new Exception("Something went wrong");
        }
    }

    public void anotherMethod() {
        try {
            int x = 10 / 0;
        } catch (Exception e) {
            e.printStackTrace(); // also bad (you should add a rule for this)
        }
    }

    public void longMethod() {
        // artificially long method to test file length / maintainability
        for (int i = 0; i < 100; i++) {
            System.out.println("Line " + i); // repeated sysout
        }
    }
}
