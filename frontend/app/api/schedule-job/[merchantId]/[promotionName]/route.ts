import { NextResponse } from "next/server";
import { GoogleAuth } from "google-auth-library";

export async function GET(
  req: Request,
  { params }: { params: { merchantId: string; promotionName: string } }
) {
  const backendUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/schedule-job/${params.merchantId}/${params.promotionName}`;

  try {
    // --- Option 1: IAM Identity Token ---
    const auth = new GoogleAuth();
    const client = await auth.getIdTokenClient(backendUrl);
    const response = await client.request({ url: backendUrl });

    // --- Option 2: Hardcoded Token (for debugging only) ---
    // const response = await fetch(backendUrl, {
    //   headers: { Authorization: `Bearer ${process.env.FIXED_BACKEND_TOKEN}` },
    // });

    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error("Schedule Job API error:", error.message || error);
    return NextResponse.json(
      { error: "Failed to schedule job" },
      { status: 500 }
    );
  }
}
