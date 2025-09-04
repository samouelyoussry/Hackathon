import { NextResponse } from "next/server";
import { GoogleAuth } from "google-auth-library";

export async function GET(
  req: Request,
  { params }: { params: { merchantId: string } }
) {
  try {
    const backendUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/promotions/${params.merchantId}`;

    // Create Google Auth client with identity token
    const auth = new GoogleAuth();
    const client = await auth.getIdTokenClient(backendUrl);

    // Send request with signed token
    const response = await client.request({ url: backendUrl });

    return NextResponse.json(response.data);
  } catch (err: any) {
    console.error("Proxy error:", err.message || err);
    return NextResponse.json(
      { error: "Proxy failed", details: err.message },
      { status: 500 }
    );
  }
}
