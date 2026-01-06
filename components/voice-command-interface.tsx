"use client";

import type React from "react";

import { useState, useRef } from "react";
import {
  Upload,
  Mic,
  MicOff,
  Loader2,
  Download,
  FileText,
  AlertCircle,
  Keyboard,
  Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  apiClient,
  type UploadResponse,
  type ProcessResponse,
} from "@/lib/api-client";

type AppState = "idle" | "uploaded" | "listening" | "processing" | "complete";

interface PDFFile {
  name: string;
  pageCount: number;
  fileId: string;
  sizeMb: number;
}

interface DetectedCommand {
  action: string;
  details: string;
  intent: string;
  parameters: {
    [key: string]: any;
  };
}

export function VoiceCommandInterface() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [pdfFile, setPdfFile] = useState<PDFFile | null>(null);
  const [transcript, setTranscript] = useState("");
  const [detectedCommand, setDetectedCommand] =
    useState<DetectedCommand | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultFileId, setResultFileId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [showTextInput, setShowTextInput] = useState(false);
  const [textCommand, setTextCommand] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  // Parse voice command to intent and parameters
  const parseVoiceCommand = (text: string): DetectedCommand | null => {
    const lower = text.toLowerCase();

    // Convert to Word
    if (
      lower.includes("convert") &&
      (lower.includes("word") || lower.includes("docx"))
    ) {
      return {
        transcript: text,
        action: "Convert PDF → Word",
        details: "Converting entire document to DOCX format",
        intent: "convert_to_word",
        parameters: {},
      };
    }

    // Extract page (single)
    const extractSingleMatch = lower.match(/extract (?:page )?(\d+)(?!\s*to)/);
    if (extractSingleMatch) {
      const page = parseInt(extractSingleMatch[1]);
      const isWord = lower.includes("word") || lower.includes("docx");
      return {
        transcript: text,
        action: `Extract Page ${page}${isWord ? " → Word" : ""}`,
        details: `Extracting page ${page}${
          isWord ? " as Word document" : " as PDF"
        }`,
        intent: "extract_pages",
        parameters: { pages: [page], format: isWord ? "docx" : "pdf" },
      };
    }

    // Extract page range
    const rangeMatch = lower.match(
      /extract (?:pages? )?(\d+) (?:to|through|-) (\d+)/
    );
    if (rangeMatch) {
      const start = parseInt(rangeMatch[1]);
      const end = parseInt(rangeMatch[2]);
      const isWord = lower.includes("word") || lower.includes("docx");
      return {
        transcript: text,
        action: `Extract Pages ${start}-${end}${isWord ? " → Word" : ""}`,
        details: `Extracting pages ${start} through ${end}${
          isWord ? " as Word document" : ""
        }`,
        intent: "extract_page_range",
        parameters: {
          startPage: start,
          endPage: end,
          format: isWord ? "docx" : "pdf",
        },
      };
    }

    // Remove page
    const removeMatch = lower.match(/remove (?:page )?(\d+)/);
    if (removeMatch) {
      const page = parseInt(removeMatch[1]);
      return {
        transcript: text,
        action: `Remove Page ${page}`,
        details: `Removing page ${page} from document`,
        intent: "remove_pages",
        parameters: { pages: [page] },
      };
    }

    // Merge pages (range)
    const mergeRangeMatch = lower.match(
      /merge (?:pages? )?(\d+) (?:to|through|-) (\d+)/
    );
    if (mergeRangeMatch) {
      const start = parseInt(mergeRangeMatch[1]);
      const end = parseInt(mergeRangeMatch[2]);
      const pages = Array.from(
        { length: end - start + 1 },
        (_, i) => start + i
      );
      return {
        transcript: text,
        action: `Merge Pages ${start}-${end}`,
        details: `Merging pages ${start} through ${end}`,
        intent: "merge_pages",
        parameters: { pages },
      };
    }

    return null;
  };

  // Real PDF upload with backend integration
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || file.type !== "application/pdf") {
      setError("Please select a valid PDF file");
      return;
    }

    setAppState("processing");
    setError(null);

    try {
      const uploadResult = await apiClient.uploadPDF(file);
      setPdfFile({
        name: uploadResult.filename,
        pageCount: uploadResult.page_count,
        fileId: uploadResult.file_id,
        sizeMb: uploadResult.size_mb,
      });
      setUploadedFile(file);
      setAppState("uploaded");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setAppState("idle");
    }
  };

  // Handle drag and drop
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file || file.type !== "application/pdf") {
      setError("Please select a valid PDF file");
      return;
    }

    setAppState("processing");
    setError(null);

    try {
      const uploadResult = await apiClient.uploadPDF(file);
      setPdfFile({
        name: uploadResult.filename,
        pageCount: uploadResult.page_count,
        fileId: uploadResult.file_id,
        sizeMb: uploadResult.size_mb,
      });
      setUploadedFile(file);
      setAppState("uploaded");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setAppState("idle");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // Real voice recognition using Web Speech API
  const startListening = () => {
    setIsListening(true);
    setAppState("listening");
    setTranscript("");
    setDetectedCommand(null);
    setError(null);

    // Check if browser supports speech recognition
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError(
        "Speech recognition not supported in this browser. Please use Chrome or Edge."
      );
      setIsListening(false);
      setAppState("uploaded");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      console.log("Voice recognition started");
    };

    recognition.onresult = (event: any) => {
      const spokenText = event.results[0][0].transcript;
      console.log("Recognized:", spokenText);
      setTranscript(spokenText);

      // Parse the command
      const command = parseVoiceCommand(spokenText);

      if (command) {
        setDetectedCommand(command);
      } else {
        setError(
          `Command not recognized: "${spokenText}". Try: "Extract page 1" or "Convert to Word"`
        );
      }

      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setError(`Voice recognition error: ${event.error}. Please try again.`);
      setIsListening(false);
      setAppState("uploaded");
    };

    recognition.onend = () => {
      setIsListening(false);
      if (!transcript) {
        setAppState("uploaded");
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
    setAppState("uploaded");
  };

  const handleTextCommand = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textCommand.trim()) return;

    setTranscript(textCommand);
    const command = parseVoiceCommand(textCommand);

    if (command) {
      setDetectedCommand(command);
    } else {
      setError(
        `Command not recognized: "${textCommand}". Try: "Extract page 1" or "Convert to Word"`
      );
    }
    setTextCommand("");
    setShowTextInput(false);
  };

  const confirmCommand = async () => {
    if (!pdfFile || !detectedCommand) return;

    setAppState("processing");
    setError(null);

    try {
      const result = await apiClient.processCommand({
        file_id: pdfFile.fileId,
        intent: detectedCommand.intent,
        parameters: detectedCommand.parameters,
      });

      setResultFileId(result.result_file_id);
      setAppState("complete");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
      setAppState("uploaded");
    }
  };

  const handleDownload = () => {
    if (resultFileId) {
      apiClient.downloadFile(resultFileId);
    }
  };

  const resetApp = () => {
    setAppState("idle");
    setPdfFile(null);
    setTranscript("");
    setDetectedCommand(null);
    setIsListening(false);
    setError(null);
    setResultFileId(null);
    setUploadedFile(null);
  };

  const performAnotherCommand = () => {
    setAppState("uploaded");
    setTranscript("");
    setDetectedCommand(null);
    setIsListening(false);
    setError(null);
    setResultFileId(null);
  };

  return (
    <div className="space-y-8 mt-12">
      {/* Error Display */}
      {error && (
        <Card className="bg-destructive/10 border-destructive animate-scale-in shadow-lg shadow-destructive/20">
          <div className="p-4 flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5 animate-pulse" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        </Card>
      )}

      {/* Upload Area */}
      {appState === "idle" && (
        <Card
          className="border-2 border-dashed border-border hover:border-primary/50 transition-all duration-300 cursor-pointer bg-card/50 backdrop-blur-sm hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/20 animate-fade-in"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="p-12 text-center space-y-4">
            <div className="flex justify-center">
              <div className="rounded-full bg-primary/10 p-6 animate-float">
                <Upload className="h-10 w-10 text-primary transition-transform duration-300 group-hover:scale-110" />
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold">Upload your PDF</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Drag & drop or click to browse
              </p>
              <p className="text-xs text-muted-foreground mt-2 opacity-70">
                Max 50MB • Up to 100 pages
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        </Card>
      )}

      {/* Uploaded File Display */}
      {pdfFile && appState !== "idle" && (
        <Card className="bg-card/80 backdrop-blur-sm">
          <div className="p-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-primary/10 p-3">
                <FileText className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-medium">{pdfFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {pdfFile.pageCount} pages • {pdfFile.sizeMb.toFixed(2)}MB
                </p>
              </div>
            </div>
            {appState === "uploaded" && (
              <Button variant="ghost" size="sm" onClick={resetApp}>
                Change
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Voice Command Area */}
      {(appState === "uploaded" || appState === "listening") && (
        <div className="space-y-6">
          <div className="flex flex-col items-center gap-6">
            {/* Microphone Button */}
            <div className="relative">
              {isListening && (
                <>
                  <div className="absolute inset-0 rounded-full bg-primary/20 animate-listening-pulse scale-150" />
                  <div className="absolute inset-0 rounded-full bg-primary/10 animate-listening-pulse scale-125 animation-delay-300" />
                </>
              )}
              <Button
                size="lg"
                onClick={isListening ? stopListening : startListening}
                className={cn(
                  "h-24 w-24 rounded-full relative z-10 transition-all duration-300 shadow-lg",
                  isListening
                    ? "bg-destructive hover:bg-destructive/90 animate-heartbeat shadow-destructive/50"
                    : "bg-primary hover:bg-primary/90 hover:scale-110 hover:shadow-primary/50 shadow-primary/30"
                )}
              >
                {isListening ? (
                  <MicOff className="h-10 w-10 animate-pulse" />
                ) : (
                  <Mic className="h-10 w-10" />
                )}
              </Button>
            </div>

            {/* Instructions */}
            <div className="text-center">
              <p className="text-lg font-medium">
                {isListening ? "Listening..." : "Click to speak your command"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Try: "Convert to Word" or "Extract page 3"
              </p>
            </div>
          </div>

          {/* Transcript Preview */}
          {transcript && (
            <Card className="bg-muted/50 backdrop-blur-sm animate-scale-in border border-primary/30">
              <div className="p-4">
                <p className="text-sm text-muted-foreground mb-1">You said:</p>
                <p className="text-lg font-medium">{transcript}</p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Command Confirmation */}
      {detectedCommand &&
        !isListening &&
        appState !== "processing" &&
        appState !== "complete" && (
          <Card className="bg-card border-primary/30 animate-scale-in shadow-lg shadow-primary/10">
            <div className="p-6 space-y-4">
              <div className="animate-slide-up">
                <p className="text-sm text-muted-foreground mb-1">
                  Command detected:
                </p>
                <h3 className="text-2xl font-semibold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  {detectedCommand.action}
                </h3>
                <p className="text-sm text-muted-foreground mt-2">
                  {detectedCommand.details}
                </p>
              </div>

              {/* Editable Parameters */}
              <div
                className="flex flex-wrap gap-2 animate-slide-up"
                style={{ animationDelay: "100ms" }}
              >
                {Object.entries(detectedCommand.parameters).map(
                  ([key, value]) => (
                    <div
                      key={key}
                      className="px-3 py-1 rounded-full bg-muted text-sm hover:bg-muted/80 transition-colors"
                    >
                      <span className="text-muted-foreground">{key}:</span>{" "}
                      <span className="font-medium">{value}</span>
                    </div>
                  )
                )}
              </div>

              <Button
                onClick={confirmCommand}
                className="w-full hover:scale-[1.02] transition-transform shadow-lg shadow-primary/20"
                size="lg"
              >
                Confirm & Process
              </Button>
            </div>
          </Card>
        )}

      {/* Processing State */}
      {appState === "processing" && (
        <Card className="bg-card/80 backdrop-blur-sm animate-scale-in border-primary/20">
          <div className="p-12 text-center space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
                <div className="relative rounded-full bg-primary/10 p-4">
                  <Loader2 className="h-12 w-12 text-primary animate-spin-ease" />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold animate-pulse">
                Processing your request...
              </h3>
              <p className="text-sm text-muted-foreground">
                {detectedCommand?.details}
              </p>
              <div className="flex items-center justify-center gap-1 mt-4">
                <div
                  className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse"
                  style={{ animationDelay: "0ms" }}
                />
                <div
                  className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse"
                  style={{ animationDelay: "150ms" }}
                />
                <div
                  className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Result Section */}
      {appState === "complete" && (
        <Card className="bg-card border-primary/30 animate-scale-in shadow-lg shadow-primary/20">
          <div className="p-8 text-center space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
                <div className="relative rounded-full bg-primary/10 p-6 animate-success-bounce">
                  <Download className="h-10 w-10 text-primary" />
                </div>
              </div>
            </div>
            <div className="animate-slide-up">
              <h3 className="text-2xl font-semibold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Ready to download!
              </h3>
              <p className="text-sm text-muted-foreground mt-2">
                Your file has been processed successfully ✨
              </p>
            </div>
            <div
              className="flex flex-col sm:flex-row gap-3 justify-center animate-slide-up"
              style={{ animationDelay: "100ms" }}
            >
              <Button
                size="lg"
                className="gap-2 hover:scale-105 transition-transform"
                onClick={handleDownload}
              >
                <Download className="h-5 w-5" />
                Download File
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={performAnotherCommand}
                className="gap-2 bg-transparent hover:scale-105 transition-transform"
              >
                <Mic className="h-5 w-5" />
                Another Command
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Text Input Mode */}
      {appState === "uploaded" && showTextInput && !detectedCommand && (
        <Card className="bg-card/80 backdrop-blur-sm animate-scale-in border-primary/20">
          <div className="p-6 space-y-4">
            <div className="text-center animate-slide-up">
              <h3 className="text-lg font-semibold mb-2">Type your command</h3>
              <p className="text-sm text-muted-foreground">
                Try: "Convert to Word" or "Extract page 3"
              </p>
            </div>
            <form
              onSubmit={handleTextCommand}
              className="flex gap-2 animate-slide-up"
              style={{ animationDelay: "100ms" }}
            >
              <Input
                type="text"
                value={textCommand}
                onChange={(e) => setTextCommand(e.target.value)}
                placeholder="e.g., Extract pages 1 to 5"
                className="flex-1 focus:ring-2 focus:ring-primary/50 transition-all"
                autoFocus
              />
              <Button
                type="submit"
                size="icon"
                disabled={!textCommand.trim()}
                className="hover:scale-110 transition-transform"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowTextInput(false)}
              className="w-full hover:bg-muted/50 transition-colors"
            >
              <Mic className="h-4 w-4 mr-2" />
              Use voice instead
            </Button>
          </div>
        </Card>
      )}

      {/* Input Mode Toggle */}
      {appState === "uploaded" &&
        !detectedCommand &&
        !showTextInput &&
        !isListening && (
          <div className="text-center">
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground gap-2"
              onClick={() => setShowTextInput(true)}
            >
              <Keyboard className="h-4 w-4" />
              Or type your command
            </Button>
          </div>
        )}
    </div>
  );
}
