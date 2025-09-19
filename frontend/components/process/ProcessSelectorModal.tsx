"use client"

import { useState, ChangeEvent } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertTriangle, CheckCircle, Loader2 } from "lucide-react"

interface ProcessSelectorModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onStartProcess: (process: string | File) => void;
}

interface FileValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

interface FileValidationState {
  isValidating: boolean;
  validationResult: FileValidationResult | null;
}

const predefinedProcesses = [
  { id: "sdlc", name: "Software Development Lifecycle" },
  { id: "marketing_campaign", name: "Marketing Campaign" },
  { id: "research_project", name: "Research Project" },
];

// File validation constants
const MAX_FILE_SIZE = 1024 * 1024; // 1MB
const ALLOWED_EXTENSIONS = ['.yaml', '.yml'];
const SUSPICIOUS_PATTERNS = [
  /!!python\//i,
  /!!map:/i,
  /&.*\*.*/, 
  /\.\.\//,
  /<script/i,
  /javascript:/i,
  /eval\s*\(/i
];

export function ProcessSelectorModal({ isOpen, onOpenChange, onStartProcess }: ProcessSelectorModalProps) {
  const [selectedProcess, setSelectedProcess] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [fileValidation, setFileValidation] = useState<FileValidationState>({
    isValidating: false,
    validationResult: null
  });

  // Client-side file validation
  const validateFile = async (file: File): Promise<FileValidationResult> => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // 1. File size validation
    if (file.size > MAX_FILE_SIZE) {
      errors.push(`File size (${Math.round(file.size / 1024)}KB) exceeds the 1MB limit`);
    }

    // 2. File extension validation
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
      errors.push(`Invalid file extension. Only ${ALLOWED_EXTENSIONS.join(', ')} files are allowed`);
    }

    // 3. Filename validation
    const baseName = file.name.substring(0, file.name.lastIndexOf('.'));
    if (!/^[a-zA-Z0-9][a-zA-Z0-9_\-]*$/.test(baseName)) {
      errors.push('Filename must start with alphanumeric character and contain only letters, numbers, hyphens, and underscores');
    }

    // 4. Content validation (if no size/extension errors)
    if (errors.length === 0) {
      try {
        const content = await file.text();
        
        // Check for suspicious patterns
        for (const pattern of SUSPICIOUS_PATTERNS) {
          if (pattern.test(content)) {
            errors.push('File contains potentially malicious content patterns');
            break;
          }
        }

        // Basic YAML structure check
        try {
          // Simple check for YAML-like structure
          if (!content.trim().includes(':')) {
            warnings.push('File may not be valid YAML format');
          }

          // Check for required process config fields
          const requiredFields = ['process_name', 'roles', 'artifacts', 'stages'];
          const missingFields = requiredFields.filter(field => !content.includes(field));
          if (missingFields.length > 0) {
            warnings.push(`File may be missing required fields: ${missingFields.join(', ')}`);
          }
        } catch {
          warnings.push('Unable to validate YAML structure');
        }

        // Server-side validation will be performed on upload
        if (warnings.length === 0 && errors.length === 0) {
          warnings.push('File passed client-side validation. Server-side validation will be performed on upload.');
        }

      } catch (error) {
        errors.push('Unable to read file content');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    
    if (!file) {
      setUploadedFile(null);
      setFileValidation({ isValidating: false, validationResult: null });
      return;
    }

    setFileValidation({ isValidating: true, validationResult: null });
    setSelectedProcess(null); // Clear dropdown selection if file is uploaded

    try {
      const validationResult = await validateFile(file);
      
      setFileValidation({ 
        isValidating: false, 
        validationResult 
      });

      // Only set the file if validation passed
      if (validationResult.isValid) {
        setUploadedFile(file);
      } else {
        setUploadedFile(null);
        // Clear the input
        event.target.value = '';
      }
    } catch (error) {
      console.error('File validation error:', error);
      setFileValidation({
        isValidating: false,
        validationResult: {
          isValid: false,
          errors: ['File validation failed due to an unexpected error'],
          warnings: []
        }
      });
      setUploadedFile(null);
      event.target.value = '';
    }
  };

  const handleStartProcess = () => {
    if (uploadedFile && fileValidation.validationResult?.isValid) {
      onStartProcess(uploadedFile);
    } else if (selectedProcess) {
      onStartProcess(selectedProcess);
    }
    onOpenChange(false); // Close modal after starting
  };

  const isStartButtonDisabled = !selectedProcess && (!uploadedFile || !fileValidation.validationResult?.isValid);

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Start a New Process</DialogTitle>
          <DialogDescription>
            Select a predefined process template or upload your own YAML configuration file.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid w-full items-center gap-1.5">
            <Label htmlFor="process-template">Select a Template</Label>
            <Select onValueChange={setSelectedProcess} value={selectedProcess || ""} disabled={!!uploadedFile}>
              <SelectTrigger id="process-template">
                <SelectValue placeholder="Choose a process..." />
              </SelectTrigger>
              <SelectContent>
                {predefinedProcesses.map((process) => (
                  <SelectItem key={process.id} value={process.id}>
                    {process.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-center">
            <span className="text-sm text-muted-foreground">OR</span>
          </div>
          <div className="grid w-full max-w-sm items-center gap-1.5">
            <Label htmlFor="custom-process">Upload a Custom Process</Label>
            <Input 
              id="custom-process" 
              type="file" 
              accept=".yaml,.yml" 
              onChange={handleFileChange} 
              disabled={fileValidation.isValidating}
            />
            
            {/* Validation Status Indicator */}
            {fileValidation.isValidating && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Validating file...
              </div>
            )}

            {/* Validation Results */}
            {fileValidation.validationResult && (
              <div className="space-y-2">
                {fileValidation.validationResult.errors.length > 0 && (
                  <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="font-medium mb-1">Validation Errors:</div>
                      <ul className="list-disc list-inside space-y-1">
                        {fileValidation.validationResult.errors.map((error, index) => (
                          <li key={index} className="text-sm">{error}</li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}
                
                {fileValidation.validationResult.warnings.length > 0 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="font-medium mb-1">Warnings:</div>
                      <ul className="list-disc list-inside space-y-1">
                        {fileValidation.validationResult.warnings.map((warning, index) => (
                          <li key={index} className="text-sm">{warning}</li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}
                
                {fileValidation.validationResult.isValid && (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="font-medium">File validated successfully</div>
                      <div className="text-sm">Ready to upload and process</div>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleStartProcess} disabled={isStartButtonDisabled}>
            Start Process
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
