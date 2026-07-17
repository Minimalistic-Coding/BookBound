from app import create_app
from app import db
from app.models import Task
# import rq 

app = create_app()
app.app_context.push()

def _set_task_progress(progress):
	if not app.config('REDIS_URL'):
		return

	job = rq.get_current_job()
	if job:
		job.meta['progress'] = progress 
		job.save_meta()
		task = db.session.get(Task, job.get_id())
		task.user.add_notification('task_progress', {'task_id': job.get_id(), 'progress': progress})

		if progress >= 100:
			task.complete = True
		db.session.commit()