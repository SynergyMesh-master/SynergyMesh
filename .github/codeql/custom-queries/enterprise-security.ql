/**
 * @name Enterprise sensitive data exposure
 * @description Detects potential exposure of enterprise sensitive data
 * @kind problem
 * @problem.severity error
 * @security-severity 8.0
 * @precision high
 * @id enterprise/sensitive-data-exposure
 * @tags security
 *       enterprise
 *       sensitive-data
 */

import javascript

from CallExpr call, StringLiteral str
where
  call.getCalleeName() = "console.log" and
  str = call.getAnArgument() and
  (
    str.getValue().matches("%password%") or
    str.getValue().matches("%secret%") or
    str.getValue().matches("%token%") or
    str.getValue().matches("%api_key%") or
    str.getValue().matches("%enterprise_id%") or
    str.getValue().matches("%private_key%") or
    str.getValue().matches("%access_token%") or
    str.getValue().matches("%auth%")
  )
select call, "Potential exposure of sensitive enterprise data: " + str.getValue()
