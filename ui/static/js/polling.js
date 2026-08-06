export async function monitorRun({id, readStatus, onUpdate, onFinish, maxAttempts = 120}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const status = await readStatus(id);
    await onUpdate(status);
    if (['completed', 'failed'].includes(status.status)) { await onFinish(status); return status; }
    await new Promise(resolve => setTimeout(resolve, Math.min(600 + attempt * 100, 2500)));
  }
  throw new Error('Search polling timed out; refresh the run later from history.');
}
