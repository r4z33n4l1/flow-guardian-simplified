import { NextRequest, NextResponse } from "next/server";

const FLOW_GUARDIAN_URL =
  process.env.FLOW_GUARDIAN_URL || "http://localhost:8090";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const files = formData.getAll("files") as File[];
    const note = formData.get("note") as string;
    const tagsRaw = formData.get("tags") as string;

    console.log(`[Upload] Received request:`, {
      filesCount: files.length,
      fileNames: files.map(f => ({ name: f.name, size: f.size, type: f.type })),
      note,
      tagsRaw,
    });

    const tags = JSON.parse(tagsRaw || "[]");

    if (files.length === 0) {
      console.error("[Upload] No files in request");
      return NextResponse.json({ error: "No files provided" }, { status: 400 });
    }

    const results = [];

    for (const file of files) {
      // Create a new FormData for each file to send to the backend
      const backendFormData = new FormData();

      // Convert File to Blob with proper filename for Node.js fetch
      const fileBuffer = await file.arrayBuffer();
      const blob = new Blob([fileBuffer], { type: file.type || "application/octet-stream" });
      backendFormData.append("file", blob, file.name);
      backendFormData.append("note", note || "");
      // Server expects comma-separated tags, not JSON
      backendFormData.append("tags", Array.isArray(tags) ? tags.join(",") : "");

      try {
        console.log(`[Upload] Uploading ${file.name} (${file.size} bytes, type: ${file.type}) to ${FLOW_GUARDIAN_URL}/documents`);

        const response = await fetch(`${FLOW_GUARDIAN_URL}/documents`, {
          method: "POST",
          body: backendFormData,
        });

        if (!response.ok) {
          const error = await response.text();
          console.error(`[Upload] Failed for ${file.name}: ${response.status} - ${error}`);
          results.push({
            filename: file.name,
            success: false,
            error: error || `Upload failed (${response.status})`,
          });
          continue;
        }

        const result = await response.json();
        console.log(`[Upload] Success for ${file.name}:`, result);
        results.push({
          filename: file.name,
          success: true,
          ...result,
        });
      } catch (error) {
        console.error(`[Upload] Exception for ${file.name}:`, error);
        results.push({
          filename: file.name,
          success: false,
          error: error instanceof Error ? error.message : "Upload failed",
        });
      }
    }

    console.log(`[Upload] Final results:`, JSON.stringify(results, null, 2));

    const allSuccess = results.every((r) => r.success);
    const anySuccess = results.some((r) => r.success);

    return NextResponse.json(
      {
        success: anySuccess,
        results,
        message: allSuccess
          ? `Successfully uploaded ${results.length} file(s)`
          : anySuccess
            ? `Uploaded ${results.filter((r) => r.success).length} of ${results.length} files`
            : "All uploads failed",
      },
      { status: allSuccess ? 200 : anySuccess ? 207 : 500 }
    );
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json(
      { error: "Failed to process upload" },
      { status: 500 }
    );
  }
}
