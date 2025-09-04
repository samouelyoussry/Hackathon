import { NextResponse } from "next/server";
import { GoogleAuth } from "google-auth-library";

export async function GET(
  req: Request,
  { params }: { params: { merchantId: string } }
) {
  try {
    const backendUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/promotions/${params.merchantId}`;


    // ✅ Option A (Recommended): Use GoogleAuth to get an ID token automatically
    const auth = new GoogleAuth();
    const client = await auth.getIdTokenClient(backendUrl);
    const response = await client.request({ url: backendUrl });

    // ✅ Option B (Debug Only): Hardcoded token (expires in ~1h)
    // const FIXED_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."; // <-- replace with gcloud auth print-identity-token
    // const response = await fetch(backendUrl, {
    //   headers: {
    //     Authorization: `Bearer ${FIXED_TOKEN}`,
    //   },
    // });

    return NextResponse.json(response.data);
  } catch (err: any) {
    console.error("Proxy error:", err.message || err);
    return NextResponse.json(
      { error: "Proxy failed", details: err.message },
      { status: 500 }
    );
  }
}
