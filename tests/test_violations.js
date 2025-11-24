// Test file with JavaScript violations
// Should trigger multiple VibeGuard rules

// SME01: var keyword
var oldSchoolVariable = "bad practice";

// HYG01: console.log in production
console.log("Debugging information");

// HYG03: debugger statement
debugger;

// SME07: alert usage
alert("Something happened!");

// STB01: Empty catch block
try {
  riskyOperation();
} catch(e) {
}

// This should be ignored
console.log("This is fine");  // vibeguard:ignore

// SEC11: innerHTML without sanitization
document.getElementById('content').innerHTML = userInput;

// SME04: Nested ternary
const value = condition1 ? value1 : condition2 ? value2 : value3;

// SME06: Long parameter list
function tooManyParams(a, b, c, d, e, f, g) {
  return a + b + c + d + e + f + g;
}

// RCT02: Index as key in React
const items = data.map((item, index) => (
  <Item key={index} data={item} />
));

// PRF01: Synchronous file operation
const data = fs.readFileSync('/path/to/file', 'utf8');
