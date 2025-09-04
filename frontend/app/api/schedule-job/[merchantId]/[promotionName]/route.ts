import { NextResponse } from "next/server";
import { GoogleAuth } from "google-auth-library";

export async function GET(
  req: Request,
  { params }: { params: { merchantId: string } }
) {
  try {
    const backendUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/promotions/${params.merchantId}`;

    const auth = new GoogleAuth();
    const client = await auth.getIdTokenClient(backendUrl);

    const response = await client.request({ url: backendUrl });

    return NextResponse.json(response.data);
  } catch (err: any) {
    console.error("Proxy error:", err.message || err);
    return NextResponse.json(
      { error: "Failed to reach backend", details: err.message },
      { status: 500 }
    );
  }
}
