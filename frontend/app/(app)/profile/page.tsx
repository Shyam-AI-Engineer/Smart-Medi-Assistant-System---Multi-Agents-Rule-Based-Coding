"use client";

import { useState, useEffect } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Loader } from "@/components/ui/Loader";
import { useAuth } from "@/hooks/useAuth";
import { useMyPatientProfile, useUpdateProfile } from "@/hooks/useVitals";
import { getApiErrorMessage } from "@/lib/api";

export default function ProfilePage() {
  const { user } = useAuth();
  const { data: profile, isLoading } = useMyPatientProfile();
  const updateProfile = useUpdateProfile();

  const [fullName, setFullName] = useState("");
  const [allergies, setAllergies] = useState("");
  const [medications, setMedications] = useState("");
  const [medicalHistory, setMedicalHistory] = useState("");
  const [emergencyContact, setEmergencyContact] = useState("");

  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name ?? "");
      setAllergies(profile.allergies ?? "");
      setMedications(profile.current_medications ?? "");
      setMedicalHistory(profile.medical_history ?? "");
      setEmergencyContact(profile.emergency_contact ?? "");
    }
  }, [profile]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSuccessMsg("");
    setErrorMsg("");

    try {
      await updateProfile.mutateAsync({
        full_name: fullName || null,
        allergies: allergies || null,
        current_medications: medications || null,
        medical_history: medicalHistory || null,
        emergency_contact: emergencyContact || null,
      });
      setSuccessMsg("Profile updated successfully.");
    } catch (err) {
      setErrorMsg(getApiErrorMessage(err, "Failed to update profile."));
    }
  }

  if (isLoading) {
    return (
      <div className="py-24">
        <Loader label="Loading profile…" />
      </div>
    );
  }

  return (
    <div className="container py-8 max-w-2xl">
      <PageHeader
        title="My Profile"
        description="View your account info and update your medical details."
      />

      {/* Account Info */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-xs text-ink-subtle uppercase font-medium mb-1">Email</p>
            <p className="text-sm text-ink">{user?.email || "—"}</p>
          </div>
          {profile?.date_of_birth && (
            <div>
              <p className="text-xs text-ink-subtle uppercase font-medium mb-1">Date of Birth</p>
              <p className="text-sm text-ink">
                {new Date(profile.date_of_birth).toLocaleDateString()}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Medical Info — editable */}
      <Card>
        <CardHeader>
          <CardTitle>Medical Information</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Full Name"
              name="fullName"
              placeholder="e.g. John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            <Textarea
              label="Allergies"
              name="allergies"
              placeholder="e.g. Penicillin, Peanuts"
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
              rows={3}
            />
            <Textarea
              label="Current Medications"
              name="medications"
              placeholder="e.g. Metformin 500mg twice daily"
              value={medications}
              onChange={(e) => setMedications(e.target.value)}
              rows={3}
            />
            <Textarea
              label="Medical History"
              name="medicalHistory"
              placeholder="e.g. Type 2 diabetes diagnosed 2019, hypertension"
              value={medicalHistory}
              onChange={(e) => setMedicalHistory(e.target.value)}
              rows={4}
            />
            <Input
              label="Emergency Contact"
              name="emergencyContact"
              placeholder="e.g. Jane Doe — +1 555-0100"
              value={emergencyContact}
              onChange={(e) => setEmergencyContact(e.target.value)}
            />

            {successMsg && (
              <p className="text-sm text-success-600 font-medium">{successMsg}</p>
            )}
            {errorMsg && (
              <p className="text-sm text-danger-600">{errorMsg}</p>
            )}

            <div className="flex justify-end">
              <Button type="submit" loading={updateProfile.isPending}>
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
