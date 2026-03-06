/**
 * ExportAuditButton Tests — Sprint 212 Track D
 *
 * Tests dropdown open/close, CSV/PDF option rendering,
 * loading state during export, and blob download trigger.
 *
 * @module frontend/src/__tests__/components/ExportAuditButton.test
 * @sprint 212
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock URL.createObjectURL / revokeObjectURL
const mockCreateObjectURL = vi.fn(() => "blob:http://localhost/fake-url");
const mockRevokeObjectURL = vi.fn();
global.URL.createObjectURL = mockCreateObjectURL;
global.URL.revokeObjectURL = mockRevokeObjectURL;

import { ExportAuditButton } from "@/components/dashboard/ExportAuditButton";

describe("ExportAuditButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window.localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue("test-token");
  });

  it("renders the export button", () => {
    render(<ExportAuditButton />);
    expect(screen.getByText("Export Audit Trail")).toBeInTheDocument();
  });

  it("opens dropdown on click and shows CSV/PDF options", () => {
    render(<ExportAuditButton />);

    // Dropdown not visible initially
    expect(screen.queryByText("Export as CSV")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Export Audit Trail"));

    expect(screen.getByText("Export as CSV")).toBeInTheDocument();
    expect(screen.getByText("Export as PDF")).toBeInTheDocument();
  });

  it("shows loading state during CSV export", async () => {
    // Fetch that never resolves to keep loading state
    mockFetch.mockReturnValue(new Promise(() => {}));

    render(<ExportAuditButton />);
    fireEvent.click(screen.getByText("Export Audit Trail"));
    fireEvent.click(screen.getByText("Export as CSV"));

    await waitFor(() => {
      expect(screen.getByText("Exporting...")).toBeInTheDocument();
    });
  });

  it("triggers blob download on successful CSV export", async () => {
    const mockBlob = new Blob(["col1,col2\na,b"], { type: "text/csv" });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: async () => mockBlob,
    });

    render(<ExportAuditButton />);
    fireEvent.click(screen.getByText("Export Audit Trail"));
    fireEvent.click(screen.getByText("Export as CSV"));

    await waitFor(() => {
      expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
      expect(mockRevokeObjectURL).toHaveBeenCalled();
    });
  });

  it("passes projectId as query parameter when provided", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: async () => new Blob(["data"]),
    });

    render(<ExportAuditButton projectId="proj-123" />);
    fireEvent.click(screen.getByText("Export Audit Trail"));
    fireEvent.click(screen.getByText("Export as CSV"));

    await waitFor(() => {
      const fetchUrl = mockFetch.mock.calls[0][0] as string;
      expect(fetchUrl).toContain("project_id=proj-123");
      expect(fetchUrl).toContain("format=csv");
    });
  });
});
