# Model Comparison

All models were trained on the same character-level corpus of fictional AI security tool names.

| Model | Class | Params | Final loss | Baseline | Time (s) | Well-formed %@0.7 | Domain-shape %@0.7 |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3 dense | `TinyQwen` | 19,456 | 0.2966 | 3.2581 | 14.08 | 100% | 56% |
| Qwen3.5 hybrid | `TinyQwen35` | 41,864 | 0.3021 | 3.2581 | 67.51 | 100% | 44% |
| Gemma-style | `TinyGemma` | 62,016 | 0.2738 | 3.2581 | 49.28 | 100% | 50% |
| DeepSeek-style sparse | `TinyDeepSeek` | 47,848 | 0.323 | 3.2581 | 37.89 | 100% | 75% |

## Samples

### Qwen3 dense

- `T=0.7`: toolscan, memorycheck, memoryguard, policyai, trustcloud, redteamguard, secretcloud, trustlab, guardsentry, agenttrace, autonomywatch, contextcheck, prompttlab, aigate, memorysentry, tokenbarrier
- `T=1.0`: jailbreakcheck, zerocheck, sessionsuite, secretsentinel, credentialdefense, zerowatch, contextfilter, jailbreakarmor, llmcloud, sessionkit, policyscanner, secretlens, memoryaudit, policyheck, secretai, jailbreakpilot
- `T=1.2`: trusthub, policyfirewall, promptai, llmpilot, jailbreakbase, zeroaudit, policysentry, secretguard, guardscan, lmemoryguard, jailbreakradar, memorystack, secretwatch, zerocloud, guardguard, lllmfilter

### Qwen3.5 hybrid

- `T=0.7`: agentstack, aibeacon, credentiallock, toolwatch, sessionscanner, contextcheck, identitywatch, identityshield, identityfirewall, secretscanner, identitylens, agentbase, contextkit, credentialscan, policyscanner, airadar
- `T=1.0`: memoryguard, agentgate, sessionshield, vault, redteamfirewall, contextops, vaulthub, zerocheck, autonomyarmor, promptsuite, policywatch, llmscan, autonomyaudit, agentgate, llmbarrier, aifirewall
- `T=1.2`: llmlens, policyla, autonomydefense, llmshield, redteamcloud, sessionsuite, autonomyaudit, credentialcloud, identityarmor, policywatch, vaultwatch, trustguard, agentstack, sessionfilter, redteamcheck, redteambeacon

### Gemma-style

- `T=0.7`: autonomystack, airadar, sessioncheck, tokenai, trustdefense, credentialai, trustlock, contextscanner, llmmops, trustlock, autonomywatch, trustscan, tokenlens, tokenbarrier, guardai, autonomysuite
- `T=1.0`: jailbreaklock, credentialhub, secretarmor, credentiallab, jailbreaklab, vaultlock, tokensentry, memoryai, credentialcheck, llmbase, llmscanner, jailbreakshield, guardaudit, secretcloud, tokentrace, secretlock
- `T=1.2`: tokenlock, credentialaudit, memorysuite, jailbreaklens, sessiontrace, redteamwarden, redteamscan, zerofirewall, zerocloud, sessiondentitrack, secretcheck, aiscan, secretaudit, llmmradguard, guardshield, tokenkit

### DeepSeek-style sparse

- `T=0.7`: jailbreakcloud, airadar, guardguard, contexttrace, toolops, trustlock, tokenwarden, aicheck, agentfilter, aigate, autonomygate, agenttrace, policyai, trusttrace, contextwatch, agentscan
- `T=1.0`: contextbase, promptmonit, contextaudit, sessionlens, vaultfirewall, autonomybarrier, redteamgate, secretdefense, trustaudit, promptbase, aiarmor, memorymonitor, guardfilter, agentradar, zerocheck, sessionbase
- `T=1.2`: ub, vaultdefense, agentcheck, trusthub, policyguard, secretmonitor, agentstacon, promptcheck, aipilot, lmbase, tokenwatch, contextarmor, zerobeacon, agentdegate, tokenpilar, jailbreakcheakclab
