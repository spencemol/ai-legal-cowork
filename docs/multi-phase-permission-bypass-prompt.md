Save this entire prompt before we start doing anything else under a new folder called `docs/multi-phase-permission-bypass-prompt.md`.

---

Then, considering the execution order and dependencies outlined in @plan.md with respect to what phase-grouped atomic tasks we have completed so far, let's follow the proper sequence and complete Phases 4-9 tasks in @tasks.md using the red-green method: per-task, write tests to fail "red" at meeting the requirement or acceptance criteria for that task initially before implementing any code, then write the code for that task and iterate just enough until the respective test(s) are passing "green".

---

After each phase, complete integration testing and output under a new `docs/phases` folder `phase_{n}.md` which provides:

1. A summary of what was implemented.
2. 0.0–1.0 confidence scoring per task on requirement and acceptance criteria coverage relative to the @tasks.md task descriptions, @plan.md, and mapping back to NFRs, FRs, and ACs in the @spec.md — 1.0 representing COMPLETE and PERFECT fulfillment.
3. According to the @plan.md high-level Phase criteria and cross-phase testability, as well as a composite of the per-task confidence scores, provide an overall Phase confidence score 0.0–1.0, 1.0 being COMPLETE and PERFECT fulfillment.
4. A summary of what we have cumulatively built so far since Phase 0 relative to the completion of the current phase.

---

After each phase, add the appropriate updates to the project-level @README.md that explain sub-repos and help run or access running sub-components.

After each phase test-first iteration cycle is complete and the post-phase documentation updates occur, using `git`, stage and commit a phase-specific message in the style of:

> "phase {n}: {description of what was done} remaining: {description of what is left to do starting with the next phase}"

---

After each phase and post-phase steps are complete, clear the Claude Code context using `/context` and continue onto the next phase until we complete Phase 9 and its post-phase steps.

DO NOT do more than what I have described and do NOT use any `git push*` commands.

Go.
