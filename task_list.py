task_list = """
        <div class="home_task_container">
          <a class="box" href="http://127.0.0.1:5000/bn?quad_id=1">
          <!-- THIS LOGIC SHOWS ALL THE TASKS THAT HAVE A MATCHING QUAD_ID -->
          <!-- FOR LOOP TO RUN THROUGH TASKS, CHECK IF MATCH -->
          {%for task in tasks %}
            {% if task.quad_id == 1 %}
              <div class="home_tasks">{{task.name}}</div>
            {%endif%}
          {%endfor%}
          </a>
        </div>
        """
