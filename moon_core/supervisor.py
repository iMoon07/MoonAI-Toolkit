import asyncio
import signal
import sys
import os

class MoonSupervisor:
    def __init__(self):
        self.tasks = set()
        self.shutdown_hooks = []
        self.stop_flag = False

    def register(self, task: asyncio.Task, name: str = None):
        self.tasks.add(task)
        task_id = id(task)
        if name is None:
            name = task.get_name() if hasattr(task, 'get_name') else "AnonymousTask"
            
        from moon_core.logger import logger as moon_logger
        moon_logger.trace_task(task_id, name, "SPAWN")
        
        def _cleanup(t):
            self.tasks.discard(t)
            if t.cancelled():
                moon_logger.trace_task(task_id, name, "CANCELLED")
            elif t.exception():
                moon_logger.trace_task(task_id, name, "EXCEPTION", details=str(t.exception()))
            else:
                moon_logger.trace_task(task_id, name, "DONE")
                
        task.add_done_callback(_cleanup)

    def add_shutdown_hook(self, fn):
        """Register a sync or async function to run on shutdown."""
        self.shutdown_hooks.append(fn)

    async def shutdown(self):
        from moon_core.logger import logger as moon_logger
        print("\n🔥 MoonSupervisor: Initiating staged shutdown...")
        moon_logger.trace_task("SYSTEM", "ShutdownPipeline", "TRIGGERED")
        self.stop_flag = True

        # Stage 1: Cancel active tasks
        print("   [Stage 1] Cancelling active tasks...")
        moon_logger.trace_task("SYSTEM", "ShutdownPipeline", "STAGE_1", "Cancelling tasks")
        for t in list(self.tasks):
            t.cancel()

        # Stage 2: Run cleanup hooks with timeout protection
        print("   [Stage 2] Executing shutdown hooks...")
        moon_logger.trace_task("SYSTEM", "ShutdownPipeline", "STAGE_2", "Executing hooks")
        for fn in self.shutdown_hooks:
            try:
                if asyncio.iscoroutinefunction(fn):
                    await asyncio.wait_for(fn(), timeout=3.0)
                else:
                    fn()
            except asyncio.TimeoutError:
                print(f"   [!] Hook {fn.__name__} timed out.")
            except Exception as e:
                print(f"   [!] Hook error: {e}")

        # Stage 3: Await task flush
        print("   [Stage 3] Waiting for tasks to flush...")
        moon_logger.trace_task("SYSTEM", "ShutdownPipeline", "STAGE_3", "Awaiting task flush")
        if self.tasks:
            done, pending = await asyncio.wait(self.tasks, timeout=3.0)
            if pending:
                print(f"   [!] {len(pending)} tasks hanging.")
            else:
                print("   [Supervisor] All tasks acknowledged cancellation.")
        else:
            print("   [Supervisor] No active tasks to flush.")

        print("   [Supervisor] Hooks completed or timed out.")
        print("   [Stage 4] Shutdown pipeline complete. Entering final exit.")
        moon_logger.trace_task("SYSTEM", "ShutdownPipeline", "STAGE_4", "Final exit")

    def install_signal(self):
        def handler(sig, frame):
            print("\n🧨 SIGINT received -> Triggering Graceful Shutdown")
            try:
                loop = asyncio.get_event_loop()
                
                def force_exit():
                    print("💀 Watchdog Timeout! Forcing os._exit(1)")
                    os._exit(1)
                    
                # Watchdog timer to ensure we never hang during shutdown
                if loop.is_running():
                    loop.call_later(10.0, force_exit)
                    future = asyncio.run_coroutine_threadsafe(self.shutdown(), loop)
                    future.add_done_callback(lambda _: os._exit(0))
                else:
                    loop.run_until_complete(self.shutdown())
                    os._exit(0)
            except Exception as e:
                print(f"Shutdown error: {e}")
                os._exit(1)

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

# Global Supervisor
moon_supervisor = MoonSupervisor()
