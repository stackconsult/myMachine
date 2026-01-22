import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="http://localhost:8001/api/copilotkit" agent="cep_machine" publicLicenseKey="ck_pub_91deedc157617c4705bddc7124314855">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
