"use client";

import { useState } from "react";
import { Eye, EyeOff, LockKeyhole } from "lucide-react";

export function PasswordField() {
  const [visible, setVisible] = useState(false);
  const Icon = visible ? EyeOff : Eye;
  return <div className="input-with-icon password-input">
    <LockKeyhole size={17} aria-hidden="true" />
    <input id="password" name="password" type={visible ? "text" : "password"} autoComplete="current-password" required />
    <button className="icon-button" type="button" aria-label={visible ? "Hide password" : "Show password"} title={visible ? "Hide password" : "Show password"} onClick={() => setVisible(!visible)}><Icon size={18} aria-hidden="true" /></button>
  </div>;
}
