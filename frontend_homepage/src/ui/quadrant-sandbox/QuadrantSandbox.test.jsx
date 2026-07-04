import { describe, expect, it, vi } from "vitest";

import { goToQuadrant } from "./QuadrantSandbox";


describe("goToQuadrant", () => {
  it("fetches the redirect endpoint and navigates to the final URL", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      redirected: true,
      url: "http://127.0.0.1:8000/center/grid/bos/",
    });
    const navigate = vi.fn();

    const result = await goToQuadrant({ fetchImpl, navigate, endpoint: "/quadrant/" });

    expect(fetchImpl).toHaveBeenCalledWith("/quadrant/", {
      method: "GET",
      redirect: "follow",
      credentials: "include",
    });
    expect(navigate).toHaveBeenCalledWith("http://127.0.0.1:8000/center/grid/bos/");
    expect(result).toBe("http://127.0.0.1:8000/center/grid/bos/");
  });

  it("falls back to JSON when the response is not redirected", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      redirected: false,
      json: vi.fn().mockResolvedValue({ url: "/domain/grid/bos-domain/" }),
    });
    const navigate = vi.fn();

    const result = await goToQuadrant({ fetchImpl, navigate, endpoint: "/quadrant/" });

    expect(navigate).toHaveBeenCalledWith("/domain/grid/bos-domain/");
    expect(result).toBe("/domain/grid/bos-domain/");
  });
});