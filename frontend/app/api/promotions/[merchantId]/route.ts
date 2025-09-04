import { NextResponse } from "next/server";

export async function GET(
  req: Request,
  { params }: { params: { merchantId: string } }
) {
  const backendUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/promotions/${params.merchantId}`;

  const response = await fetch(backendUrl, {
    headers: {
      Authorization: req.headers.get("authorization") || "",
    },
  });

  const data = await response.json();
  return NextResponse.json(data);
}
