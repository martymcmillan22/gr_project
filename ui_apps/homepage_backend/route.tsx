import { lazy } from "react";

export const HomepageBackendRoute = {
    path: "/homepage",
    component: lazy(() => import("./pages/HomepageBackendPage")),
};
