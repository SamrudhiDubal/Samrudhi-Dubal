const mongoose = require('mongoose');

const applicationSchema = new mongoose.Schema(
  {
    job: { type: mongoose.Schema.Types.ObjectId, ref: 'Job', required: true },
    candidate: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    resumePath: { type: String, required: true },
    resumeOriginalName: { type: String },
    resumeText: { type: String },
    coverLetter: { type: String, trim: true },
    extractedSkills: [{ type: String, trim: true, lowercase: true }],
    matchScore: { type: Number, default: 0, min: 0, max: 100 },
    matchDetails: {
      skillMatchPercent: { type: Number, default: 0 },
      textSimilarityPercent: { type: Number, default: 0 },
      experienceFitPercent: { type: Number, default: null },
      candidateYearsOfExperience: { type: Number, default: null },
      educationLevel: { type: String, default: null },
      matchedSkills: [{ type: String }],
      missingSkills: [{ type: String }],
      semanticScore: { type: Number, default: null },
      semanticSummary: { type: String, default: null },
    },
    status: {
      type: String,
      enum: ['applied', 'shortlisted', 'rejected', 'hired'],
      default: 'applied',
    },
  },
  { timestamps: true }
);

applicationSchema.index({ job: 1, candidate: 1 }, { unique: true });

module.exports = mongoose.model('Application', applicationSchema);
