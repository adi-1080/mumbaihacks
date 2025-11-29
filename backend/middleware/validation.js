const Joi = require('joi');

/**
 * Validate appointment booking request
 */
exports.validateAppointment = (req, res, next) => {
  // Log the incoming request body
  console.log('📥 Incoming booking request:', JSON.stringify(req.body, null, 2));
  
  const schema = Joi.object({
    name: Joi.string().min(2).max(100).required(),
    contact_number: Joi.string()
      .pattern(/^[+]?[\d\s-()]+$/)
      .required(),
    symptoms: Joi.string().min(5).max(500).required(),
    location: Joi.string().optional().allow(''),
    age: Joi.number().integer().min(1).max(150).optional(),
    gender: Joi.string().valid('Male', 'Female', 'Other').optional(),
    emergency_level: Joi.string()
      .valid('NORMAL', 'MODERATE', 'PRIORITY', 'CRITICAL', 'HIGH')
      .optional(),
    urgency_score: Joi.number().integer().min(1).max(10).optional(),
    // Doctor information fields
    doctor_name: Joi.string().max(100).optional(),
    doctor_specialty: Joi.string().max(100).optional(),
    doctor_hospital: Joi.string().max(200).optional(),
    doctor_fee: Joi.string().max(50).optional(),
  });
  
  const { error } = schema.validate(req.body);
  
  if (error) {
    console.log('❌ Validation error details:', error.details);
    console.log('❌ Failed field:', error.details[0].path);
    console.log('❌ Error message:', error.details[0].message);
    return res.status(400).json({
      success: false,
      message: 'Validation error',
      errors: error.details.map((detail) => detail.message),
    });
  }

  console.log('✅ Validation passed');
  next();
};

/**
 * Validate location update request
 */
exports.validateLocation = (req, res, next) => {
  const schema = Joi.object({
    latitude: Joi.number().min(-90).max(90).required(),
    longitude: Joi.number().min(-180).max(180).required(),
    address: Joi.string().optional().allow(''),
  });

  const { error } = schema.validate(req.body);

  if (error) {
    return res.status(400).json({
      success: false,
      message: 'Validation error',
      errors: error.details.map((detail) => detail.message),
    });
  }

  next();
};
