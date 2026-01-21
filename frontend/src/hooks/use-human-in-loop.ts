"use client";

import { useHumanInTheLoop } from "@copilotkit/react-core";
import { useState } from "react";

// Human-in-the-Loop configurations for CEP Machine
export function useBookingApproval() {
  const [pendingBookings, setPendingBookings] = useState<any[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Configure HITL for booking approvals
  const bookingApproval = useHumanInTheLoop({
    name: "booking_approval",
    description: "Approve or reject meeting bookings",
    handler: async (bookingData: any) => {
      setIsProcessing(true);
      try {
        // Show approval dialog to user
        const approved = await showApprovalDialog(bookingData);
        
        // Send decision to backend
        const response = await fetch("/api/bookings/approve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            booking_id: bookingData.id,
            approved,
            notes: bookingData.notes
          }),
        });
        
        const result = await response.json();
        
        // Update pending bookings list
        if (approved) {
          setPendingBookings(prev => prev.filter(b => b.id !== bookingData.id));
        }
        
        return result;
      } catch (error) {
        console.error("Approval error:", error);
        return { error: "Failed to process approval" };
      } finally {
        setIsProcessing(false);
      }
    },
  });

  // Helper function to show approval dialog
  const showApprovalDialog = (bookingData: any): Promise<boolean> => {
    return new Promise((resolve) => {
      // Create modal dialog
      const modal = document.createElement("div");
      modal.className = "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50";
      modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <h3 class="text-lg font-semibold mb-4">Approve Meeting?</h3>
          <div class="mb-4">
            <p class="text-sm text-gray-600">Meeting Details:</p>
            <ul class="mt-2 space-y-1">
              <li><strong>With:</strong> ${bookingData.prospect_name}</li>
              <li><strong>Date:</strong> ${bookingData.date}</li>
              <li><strong>Time:</strong> ${bookingData.time}</li>
              <li><strong>Duration:</strong> ${bookingData.duration}</li>
            </ul>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Notes (optional):</label>
            <textarea id="approval-notes" class="w-full p-2 border rounded" rows="3"></textarea>
          </div>
          <div class="flex justify-end space-x-2">
            <button id="reject-btn" class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
              Reject
            </button>
            <button id="approve-btn" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
              Approve
            </button>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      const handleApprove = () => {
        bookingData.notes = (document.getElementById("approval-notes") as HTMLTextAreaElement).value;
        document.body.removeChild(modal);
        resolve(true);
      };
      
      const handleReject = () => {
        bookingData.notes = (document.getElementById("approval-notes") as HTMLTextAreaElement).value;
        document.body.removeChild(modal);
        resolve(false);
      };
      
      (document.getElementById("approve-btn") as HTMLButtonElement).onclick = handleApprove;
      (document.getElementById("reject-btn") as HTMLButtonElement).onclick = handleReject;
    });
  };

  return {
    bookingApproval,
    pendingBookings,
    isProcessing,
  };
}

export function useCreditDecision() {
  const [decisions, setDecisions] = useState<any[]>([]);
  const [currentDecision, setCurrentDecision] = useState<any>(null);

  // Configure HITL for credit limit decisions
  const creditDecision = useHumanInTheLoop({
    name: "credit_decision",
    description: "Approve or reject credit applications",
    handler: async (applicationData: any) => {
      try {
        // Show decision dialog
        const decision = await showCreditDecisionDialog(applicationData);
        
        // Send decision to backend
        const response = await fetch("/api/credit/decide", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            application_id: applicationData.id,
            decision: decision.approved,
            limit: decision.limit,
            reason: decision.reason
          }),
        });
        
        const result = await response.json();
        
        // Update decisions list
        setDecisions(prev => [...prev, {
          ...decision,
          application_id: applicationData.id,
          timestamp: new Date().toISOString()
        }]);
        
        return result;
      } catch (error) {
        console.error("Decision error:", error);
        return { error: "Failed to process decision" };
      }
    },
  });

  // Helper function to show credit decision dialog
  const showCreditDecisionDialog = (applicationData: any): Promise<any> => {
    return new Promise((resolve) => {
      const modal = document.createElement("div");
      modal.className = "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50";
      modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <h3 class="text-lg font-semibold mb-4">Credit Decision</h3>
          <div class="mb-4">
            <p class="text-sm text-gray-600">Application Details:</p>
            <ul class="mt-2 space-y-1">
              <li><strong>Applicant:</strong> ${applicationData.applicant_name}</li>
              <li><strong>Amount:</strong> $${applicationData.requested_amount.toLocaleString()}</li>
              <li><strong>Score:</strong> ${applicationData.credit_score}</li>
              <li><strong>Income:</strong> $${applicationData.annual_income.toLocaleString()}/year</li>
            </ul>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Credit Limit:</label>
            <input type="number" id="credit-limit" class="w-full p-2 border rounded" 
                   value="${applicationData.requested_amount}" min="0" step="1000">
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Reason:</label>
            <textarea id="decision-reason" class="w-full p-2 border rounded" rows="3" 
                      placeholder="Enter reason for decision..."></textarea>
          </div>
          <div class="flex justify-end space-x-2">
            <button id="reject-btn" class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
              Reject
            </button>
            <button id="approve-btn" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
              Approve
            </button>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      const handleApprove = () => {
        resolve({
          approved: true,
          limit: parseInt((document.getElementById("credit-limit") as HTMLInputElement).value),
          reason: (document.getElementById("decision-reason") as HTMLTextAreaElement).value
        });
        document.body.removeChild(modal);
      };
      
      const handleReject = () => {
        resolve({
          approved: false,
          limit: 0,
          reason: (document.getElementById("decision-reason") as HTMLTextAreaElement).value
        });
        document.body.removeChild(modal);
      };
      
      (document.getElementById("approve-btn") as HTMLButtonElement).onclick = handleApprove;
      (document.getElementById("reject-btn") as HTMLButtonElement).onclick = handleReject;
    });
  };

  return {
    creditDecision,
    decisions,
    currentDecision,
  };
}

export function useContentApproval() {
  const [pendingContent, setPendingContent] = useState<any[]>([]);
  const [isReviewing, setIsReviewing] = useState(false);

  // Configure HITL for content approval
  const contentApproval = useHumanInTheLoop({
    name: "content_approval",
    description: "Review and approve generated content",
    handler: async (contentData: any) => {
      setIsReviewing(true);
      try {
        // Show content review dialog
        const review = await showContentReviewDialog(contentData);
        
        // Send review to backend
        const response = await fetch("/api/content/approve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content_id: contentData.id,
            approved: review.approved,
            edits: review.edits,
            feedback: review.feedback
          }),
        });
        
        const result = await response.json();
        
        // Update pending content
        if (review.approved) {
          setPendingContent(prev => prev.filter(c => c.id !== contentData.id));
        } else if (review.edits) {
          // Content needs edits, keep in pending
          setPendingContent(prev => 
            prev.map(c => c.id === contentData.id ? { ...c, status: "needs_edits", edits: review.edits } : c)
          );
        }
        
        return result;
      } catch (error) {
        console.error("Content approval error:", error);
        return { error: "Failed to process approval" };
      } finally {
        setIsReviewing(false);
      }
    },
  });

  // Helper function to show content review dialog
  const showContentReviewDialog = (contentData: any): Promise<any> => {
    return new Promise((resolve) => {
      const modal = document.createElement("div");
      modal.className = "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50";
      modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
          <h3 class="text-lg font-semibold mb-4">Review Content</h3>
          <div class="mb-4">
            <div class="bg-gray-50 p-4 rounded">
              <p class="text-sm text-gray-600 mb-2">Type: ${contentData.type}</p>
              <div class="prose max-w-none">
                ${contentData.content}
              </div>
            </div>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Feedback:</label>
            <textarea id="content-feedback" class="w-full p-2 border rounded" rows="3" 
                      placeholder="Enter feedback..."></textarea>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Edits (if needed):</label>
            <textarea id="content-edits" class="w-full p-2 border rounded" rows="4" 
                      placeholder="Suggested edits..."></textarea>
          </div>
          <div class="flex justify-end space-x-2">
            <button id="reject-btn" class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
              Reject
            </button>
            <button id="edit-btn" class="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600">
              Needs Edits
            </button>
            <button id="approve-btn" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
              Approve
            </button>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      const handleApprove = () => {
        resolve({
          approved: true,
          edits: null,
          feedback: (document.getElementById("content-feedback") as HTMLTextAreaElement).value
        });
        document.body.removeChild(modal);
      };
      
      const handleEdit = () => {
        resolve({
          approved: false,
          edits: (document.getElementById("content-edits") as HTMLTextAreaElement).value,
          feedback: (document.getElementById("content-feedback") as HTMLTextAreaElement).value
        });
        document.body.removeChild(modal);
      };
      
      const handleReject = () => {
        resolve({
          approved: false,
          edits: null,
          feedback: (document.getElementById("content-feedback") as HTMLTextAreaElement).value
        });
        document.body.removeChild(modal);
      };
      
      (document.getElementById("approve-btn") as HTMLButtonElement).onclick = handleApprove;
      (document.getElementById("edit-btn") as HTMLButtonElement).onclick = handleEdit;
      (document.getElementById("reject-btn") as HTMLButtonElement).onclick = handleReject;
    });
  };

  return {
    contentApproval,
    pendingContent,
    isReviewing,
  };
}
