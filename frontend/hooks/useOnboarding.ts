"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./useAuth";

export function useOnboarding() {
  const { user } = useAuth();
  const [show, setShow] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!user || user.role !== "patient") {
      setChecked(true);
      return;
    }
    const key = `onboarding_done_${user.user_id}`;
    const done = localStorage.getItem(key) === "1";
    setShow(!done);
    setChecked(true);
  }, [user]);

  const complete = useCallback(() => {
    if (!user) return;
    localStorage.setItem(`onboarding_done_${user.user_id}`, "1");
    setShow(false);
  }, [user]);

  return { showWizard: checked && show, completeWizard: complete };
}
