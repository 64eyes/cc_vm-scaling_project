package utilities;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * HTTP Request Utility Class.
 */
public final class HttpRequest {

    /**
     * Private Constructor.
     */
    private HttpRequest() {
    }

    /**
     * Make a HTTP GET request to a URL.
     *
     * @param url Input URL
     * @return response of the request
     * @throws IOException when network failure occurs
     */

    public static String sendGet(final String url) throws IOException {

        URL obj = new URL(url);
        HttpURLConnection con = (HttpURLConnection) obj.openConnection();
        con.setRequestMethod("GET");
        con.getResponseCode();
        BufferedReader in = new BufferedReader(
                new InputStreamReader(con.getInputStream()));
        String inputLine;
        StringBuilder response = new StringBuilder();
        while ((inputLine = in.readLine()) != null) {
            response.append(inputLine);
            response.append("\n");
        }
        in.close();
        return response.toString();
    }
}
