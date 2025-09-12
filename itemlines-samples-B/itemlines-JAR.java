import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.List;
import java.util.Arrays;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

public class Main {
    // --- DATA ---
    private static List<String> itemlines = Arrays.asList(
        "101 18V Cordless Drill 2 89.99",
        "102 6-inch Wood Clamp 4 12.50",
        "103 Carpenter's Hammer 1 19.99"
    );

    static class Handler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (exchange.getRequestURI().getPath().equals("/itemlines")) {
                String response = "";
                for (String t : itemlines) {
                    response += "<custom>" + t + "</custom>\n";
                }
                exchange.sendResponseHeaders(200, response.getBytes().length);
                OutputStream os = exchange.getResponseBody();
                os.write(response.getBytes());
                os.close();
            } else {
                exchange.sendResponseHeaders(404, -1);
            }
        }
    }

    // -------------------------
    // Runner
    // -------------------------
    public static void runHttpServer(String host, int port) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(host, port), 0);
        server.createContext("/itemlines", new Handler());
        System.out.println("[A] Legacy server at http://" + host + ":" + port + "/itemlines");
        server.start();
    }

    public static void main(String[] args) {
        // Start legacy HTTP server
        Thread serverThread = new Thread(() -> {
            try {
                runHttpServer("0.0.0.0", 5051);
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
        serverThread.setDaemon(true);
        serverThread.start();
    }
}
