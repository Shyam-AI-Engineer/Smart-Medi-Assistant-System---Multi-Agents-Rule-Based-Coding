"use client";

import { useState } from "react";
import { AlertCircle, Wifi, WifiOff, Send } from "lucide-react";
import { useVitalsWebSocket, type VitalsMessage } from "@/hooks/useVitalsWebSocket";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function RealtimeVitalsWidget({ patientId }: { patientId: string }) {
  const [showWidget, setShowWidget] = useState(false);
  const { isConnected, lastMessage, error, sendVitals } =
    useVitalsWebSocket(patientId, showWidget);

  const [formValues, setFormValues] = useState<VitalsMessage>({});

  const handleInputChange = (field: keyof VitalsMessage, value: string) => {
    setFormValues((prev) => ({
      ...prev,
      [field]: value ? parseFloat(value) : undefined,
    }));
  };

  const handleSend = () => {
    if (Object.keys(formValues).length === 0) {
      return;
    }
    sendVitals(formValues);
    setFormValues({});
  };

  if (!showWidget) {
    return (
      <Button
        onClick={() => setShowWidget(true)}
        variant="outline"
        className="mb-4"
      >
        Open Real-time Monitor
      </Button>
    );
  }

  return (
    <Card className="p-6 mb-6 border-blue-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">Real-time Monitor</h3>
          {isConnected ? (
            <div className="flex items-center gap-1 text-green-600">
              <Wifi className="size-4" />
              <span className="text-sm">Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-red-600">
              <WifiOff className="size-4" />
              <span className="text-sm">Disconnected</span>
            </div>
          )}
        </div>
        <Button
          onClick={() => setShowWidget(false)}
          variant="ghost"
          size="sm"
        >
          Close
        </Button>
      </div>

      {error && (
        <div className="flex items-start gap-2 px-3 py-2 rounded-md bg-red-50 border border-red-200 text-sm text-red-700 mb-4">
          <AlertCircle className="size-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-3 mb-4">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-sm font-medium mb-1">
              Heart Rate (bpm)
            </label>
            <Input
              type="number"
              value={formValues.heart_rate ?? ""}
              onChange={(e) => handleInputChange("heart_rate", e.target.value)}
              placeholder="85"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Temperature (°C)
            </label>
            <Input
              type="number"
              step="0.1"
              value={formValues.temperature ?? ""}
              onChange={(e) => handleInputChange("temperature", e.target.value)}
              placeholder="37.2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Systolic (mmHg)
            </label>
            <Input
              type="number"
              value={formValues.blood_pressure_systolic ?? ""}
              onChange={(e) =>
                handleInputChange("blood_pressure_systolic", e.target.value)
              }
              placeholder="120"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Diastolic (mmHg)
            </label>
            <Input
              type="number"
              value={formValues.blood_pressure_diastolic ?? ""}
              onChange={(e) =>
                handleInputChange("blood_pressure_diastolic", e.target.value)
              }
              placeholder="80"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Oxygen (%)
            </label>
            <Input
              type="number"
              value={formValues.oxygen_saturation ?? ""}
              onChange={(e) =>
                handleInputChange("oxygen_saturation", e.target.value)
              }
              placeholder="98"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Respiratory Rate
            </label>
            <Input
              type="number"
              value={formValues.respiratory_rate ?? ""}
              onChange={(e) =>
                handleInputChange("respiratory_rate", e.target.value)
              }
              placeholder="16"
            />
          </div>
        </div>

        <Button
          onClick={handleSend}
          disabled={!isConnected || Object.keys(formValues).length === 0}
          className="w-full"
        >
          <Send className="size-4 mr-2" />
          Send & Analyze
        </Button>
      </div>

      {lastMessage && lastMessage.status === "success" && (
        <div className="border-t pt-4">
          <h4 className="font-semibold mb-2">Last Analysis</h4>
          <div className="bg-blue-50 p-3 rounded-md text-sm space-y-1">
            <p>
              <strong>Status:</strong>{" "}
              {lastMessage.analysis?.overall_status || "N/A"}
            </p>
            <p>
              <strong>Assessment:</strong>{" "}
              {lastMessage.analysis?.overall_assessment || "N/A"}
            </p>
            {lastMessage.analysis?.recommendations && (
              <div>
                <strong>Recommendations:</strong>
                <ul className="list-disc list-inside mt-1">
                  {lastMessage.analysis.recommendations.slice(0, 2).map(
                    (rec: string, i: number) => (
                      <li key={i} className="text-xs">
                        {rec}
                      </li>
                    )
                  )}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
