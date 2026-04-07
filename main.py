import math
import random
import asyncio
import pyray as pr

async def main():

    pr.init_window(1280, 720, "Atividade 01")
    pr.set_exit_key(0)
    pr.rl_set_line_width(3)
    camera = pr.Camera3D((0, 0.5, 0), (1, 0.5, 1), (0, 1, 0), 60, pr.CAMERA_PERSPECTIVE)
    light_cam = pr.Camera3D((0, 0.5, 0), (1, 0.5, 1), (0, 1, 0), 20, pr.CAMERA_ORTHOGRAPHIC)

    cube_mesh = pr.gen_mesh_cube(1, 1, 1)
    cube_model = pr.load_model_from_mesh(cube_mesh)

    floor_mesh = pr.gen_mesh_plane(1, 1, 1, 1)
    floor_model = pr.load_model_from_mesh(floor_mesh)

    img = pr.gen_image_perlin_noise(256, 256, 0, 0, 12.0)
    pr.image_color_brightness(img, 80)
    texture = pr.load_texture_from_image(img)
    pr.unload_image(img)

    cube_model.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture
    floor_model.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture

    # Carregar textura do logo para a esfera
    logo_img = pr.load_image("assets/img/feilogo.jpg")
    pr.image_flip_horizontal(logo_img)
    logo_texture = pr.load_texture_from_image(logo_img)
    pr.unload_image(logo_img)
    sphere_mesh = pr.gen_mesh_sphere(0.5, 16, 16)
    sphere_model = pr.load_model_from_mesh(sphere_mesh)
    sphere_model.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = logo_texture

    shader = pr.load_shader("shaders/vertex_shader.vs", "shaders/fragment_shader.fs")
    shadow_shader = pr.load_shader("shaders/vertex_shader.vs", "shaders/shadowpass.fs")

    floor_model.materials[0].shader = shader
    cube_model.materials[0].shader = shader
    sphere_model.materials[0].shader = shader

    light_dir = pr.Vector3(1.0, -1.0, 0.5)
    light_color = pr.Vector3(1.0, 0.8, 0.5)

    light_dir_loc = pr.get_shader_location(shader, "lightDir")
    light_color_loc = pr.get_shader_location(shader, "lightColor")

    pr.set_shader_value(shader, light_dir_loc, light_dir, pr.SHADER_UNIFORM_VEC3)
    pr.set_shader_value(shader, light_color_loc, light_color, pr.SHADER_UNIFORM_VEC3)
    light_color_list_loc = pr.get_shader_location(shader, "lightColorList")
    light_pos_loc = pr.get_shader_location(shader, "lightPos")
    light_count_loc = pr.get_shader_location(shader, "lightCount")

    light_colors = pr.ffi.new("float[]", [0, 0, 1, 1, 1, 0, 0.5, 0, 0.5])
    light_count = 3
    pr.set_shader_value_v(shader, light_color_list_loc, light_colors, pr.SHADER_UNIFORM_VEC3, light_count)
    pr.set_shader_value(shader, light_count_loc, pr.ffi.new("int *", light_count), pr.SHADER_UNIFORM_INT)

    shadow_rt = load_shadowmap_render_texture(1024, shader)

    player = Player()
    maze = Maze()
    agent = MazeAgent(maze)
    game_state = "pause"
    level = 0
    msg = "Clique M1 para continuar"
    global pointer_locked
    pointer_locked = 1
    
    player_wins = 0
    agent_wins = 0
    final_winner = None

    pr.init_audio_device()

    music = pr.load_music_stream("assets/music/System of a Down - Aerials (Remastered 2021).mp3")
    music_playing = False

    while not pr.window_should_close():
        pr.update_music_stream(music)
        if pr.is_key_down(pr.KEY_ESCAPE) or not pointer_locked:
            game_state = "pause"
            msg = "Clique M1 para continuar"
            pr.enable_cursor()

        if pr.is_key_pressed(pr.KEY_SPACE):
            if music_playing:
                pr.stop_music_stream(music)
            else:
                pr.play_music_stream(music)
            music_playing = not music_playing

        if game_state == "play":
            player.controls(maze)
            agent.update(maze)
            if maze.exit == (int(player.pos.x), int(player.pos.z)):
                player_wins += 1
                if player_wins >= 3:
                    game_state = "game_over"
                    final_winner = "player"
                    msg = "Você venceu a partida! Pressione M1 para sair"
                else:
                    game_state = "pause"
                    msg = f"Você ganhou! ({player_wins}/3) Clique M1 para continuar"
                    player = Player()
                    maze = Maze(level * 2 + 15)
                    agent = MazeAgent(maze, 1 + level / 5)
                    level += 1
            elif agent.done:
                agent_wins += 1
                if agent_wins >= 3:
                    game_state = "game_over"
                    final_winner = "agent"
                    msg = "Você perdeu sua vaga! Pressione M1 para sair"
                else:
                    game_state = "pause"
                    msg = f"Você perdeu! ({agent_wins}/3) Clique M1 para tentar novamente"
                    player = Player()
                    maze = Maze(level * 2 + 15)
                    agent = MazeAgent(maze, 1 + level / 5)
                    level += 1

        camera.position = player.pos

        camera.target = pr.vector3_add(player.pos, player.direction)

        light_positions = pr.ffi.new(
            "float[]", [agent.pos.x, 0.5, agent.pos.z, maze.exit[0] + 0.5, 0.7, maze.exit[1] + 0.5, player.pos.x, 0.5, player.pos.z]
        )

        pr.set_shader_value_v(shader, light_pos_loc, light_positions, pr.SHADER_UNIFORM_VEC3, light_count)

        update_shadow(
            shader,
            shadow_shader,
            shadow_rt,
            cube_model,
            light_cam,
            maze,
            agent,
            player,
            pr.vector3_add(player.pos, pr.vector3_scale(light_dir, 10.0)),
            light_dir,
        )
        pr.begin_drawing()
        pr.clear_background(pr.SKYBLUE)
        pr.begin_mode_3d(camera)
        pr.draw_sphere((player.pos.x - light_dir.x * 500, -light_dir.y * 500, player.pos.z - light_dir.z * 500), 25, pr.YELLOW)
        pr.draw_model_ex(
            floor_model, (maze.size / 2, 0, maze.size / 2), (0, 1, 0), 0, (maze.size, 1, maze.size), (230, 190, 250, 255)
        )


        for i in range(maze.size):
            for j in range(maze.size):
                if maze.maze[i][j] != 0:
                    height = maze.heights[i][j]

                    pr.draw_model_ex(cube_model, (i + 0.5, 0.5 * height, j + 0.5), (0, 1, 0), 0, (1, height, 1), maze.colors[i][j])
                    pr.draw_cube_wires((i + 0.5, 0.5 * height, j + 0.5), 1, height, 1, pr.BLACK)

        # Desenhar esfera com logo no local do exit, flutuando
        sphere_pos = pr.Vector3(maze.exit[0] + 0.5, 1.0 + 0.3 * math.sin(pr.get_time() * 2), maze.exit[1] + 0.5)
        pr.draw_model_ex(sphere_model, sphere_pos, (0, 1, 0), pr.get_time() * 50, (1, 1, 1), pr.WHITE)
        
        pr.draw_sphere((agent.pos.x, 0.5, agent.pos.z), 0.1, pr.BLUE)
        pr.draw_capsule(agent.pos, (agent.pos.x, 0.5, agent.pos.z), 0.25, 10, 4, (50, 100, 200, 100))

        pr.end_mode_3d()
        if game_state != "play":
            pr.draw_text(f"Placar: Você {player_wins}/3 | Outro candidato {agent_wins}/3", 50, 150, 35, pr.WHITE)
            pr.draw_text(f"Level atual: {level+1}", 50, 100, 40, pr.WHITE)
            pr.draw_text(msg, 50, 50, 40, pr.WHITE)
            if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                if game_state == "game_over":
                    break
                game_state = "play"
                pr.disable_cursor()
        else:
            pr.draw_text(f"Placar: Você {player_wins}/3 | Outro candidato {agent_wins}/3", 50, 50, 35, pr.WHITE)
                
        pr.draw_fps(10, 10)
        pr.end_drawing()
        await asyncio.sleep(0)

    pr.unload_texture(texture)
    pr.unload_texture(logo_texture)
    pr.unload_model(sphere_model)
    pr.unload_music_stream(music)
    pr.close_audio_device()
    pr.close_window()


class Player:
    def __init__(self):
        self.pos = pr.Vector3(1.5, 0.5, 1.5)
        self.yaw = 0
        self.pitch = 0
        self.sensitivity = 0.003
        self.direction = pr.Vector3(1, 0, 1)
        self.speed = 2
        pr.disable_cursor()

    def controls(self, maze):
        speed = pr.get_frame_time() * self.speed
        mouse_delta = pr.get_mouse_delta()
        self.yaw -= mouse_delta.x * self.sensitivity
        self.pitch = max(-1.57, min(1.57, self.pitch - mouse_delta.y * self.sensitivity))
        sin_yaw, cos_yaw = math.sin(self.yaw), math.cos(self.yaw)


        self.direction.x = math.cos(self.pitch) * sin_yaw
        self.direction.y = math.sin(self.pitch)
        self.direction.z = math.cos(self.pitch) * cos_yaw

        forward = (pr.is_key_down(pr.KEY_W) or pr.is_mouse_button_down(pr.MOUSE_BUTTON_LEFT)) - pr.is_key_down(pr.KEY_S)
        sideward = pr.is_key_down(pr.KEY_D) - pr.is_key_down(pr.KEY_A)

        if forward != 0 and sideward != 0:
            speed *= 0.707

        nx, nz = self.pos.x, self.pos.z

        nx += speed * (sin_yaw * forward - cos_yaw * sideward)
        nz += speed * (cos_yaw * forward + sin_yaw * sideward)

        if maze.no_collision(nx, nz):
            self.pos.x, self.pos.z = nx, nz
        elif maze.no_collision(nx, self.pos.z):
            self.pos.x = nx
        if maze.no_collision(self.pos.x, nz):
            self.pos.z = nz


class Maze:
    def __init__(self, size=15):
        self.size = size
        self.maze = [[1] * self.size for _ in range(self.size)]
        self.colors = [[[random.randint(0, 255) for _ in range(3)] + [255] for _ in range(self.size)] for _ in range(self.size)]
        self.heights = [[round(random.uniform(0.2, 2), 1) for _ in range(self.size)] for _ in range(self.size)]

        def carve(x, y):
            self.maze[x][y] = 0
            dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
            random.shuffle(dirs)

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.size - 1 and 1 <= ny < self.size - 1 and self.maze[nx][ny] == 1:
                    self.maze[x + dx // 2][y + dy // 2] = 0
                    carve(nx, ny)

        carve(1, 1)
        for _ in range(self.size * 2):
            self.maze[random.randint(1, self.size - 2)][random.randint(1, self.size - 2)] = 0

        self.exit = random.randint(1, self.size - 2), random.randint(1, self.size - 2)
        self.maze[self.exit[0]][self.exit[1]] = 0

    def no_collision(self, nx, nz):
        if (
            self.maze[int(nx + 0.1)][int(nz + 0.1)] != 0
            or self.maze[int(nx + 0.1)][int(nz)] != 0
            or self.maze[int(nx)][int(nz + 0.1)] != 0
            or self.maze[int(nx - 0.1)][int(nz)] != 0
            or self.maze[int(nx)][int(nz - 0.1)] != 0
            or self.maze[int(nx - 0.1)][int(nz - 0.1)] != 0
        ):
            return 0
        return 1


class MazeAgent:
    def __init__(self, maze, speed=1):
        self.pos = pr.Vector3(1.1, 0, 1.1)
        self.speed = speed
        self.done = False
        self.heatmap = [[0] * maze.size for _ in range(maze.size)]
        self.target_cell = (1, 1)

    def _choose_next_cell(self, maze):
        min_heat, x, z = 99999, int(self.pos.x), int(self.pos.z)
        for dx, dz in random.sample([(-1, 0), (1, 0), (0, -1), (0, 1)], 4):
            nx, nz = x + dx, z + dz
            if maze.maze[nx][nz] == 0:
                if self.heatmap[nx][nz] < min_heat:
                    min_heat = self.heatmap[nx][nz]
                    position = (nx, nz)
                if maze.exit == (nx, nz):
                    return (nx, nz)
        return position

    def update(self, maze):
        if self.done:
            return

        dx, dz = self.target_cell[0] + 0.5 - self.pos.x, self.target_cell[1] + 0.5 - self.pos.z
        dist2 = dx * dx + dz * dz

        if dist2 < 0.0005:
            self.heatmap[self.target_cell[0]][self.target_cell[1]] += 1
            if self.target_cell == maze.exit:
                self.done = True
            else:
                self.target_cell = self._choose_next_cell(maze)

        speed = pr.get_frame_time() * self.speed / math.sqrt(dist2 + 1e-16)
        nx, nz = self.pos.x + dx * speed, self.pos.z + dz * speed
        if maze.no_collision(nx, self.pos.z):
            self.pos.x = nx
        if maze.no_collision(self.pos.x, nz):
            self.pos.z = nz


def load_shadowmap_render_texture(size, shader, shadow_slot=10):
    shadow_rt = pr.load_render_texture(size, size)
    pr.rl_enable_shader(shader.id)
    pr.rl_active_texture_slot(shadow_slot)
    pr.rl_enable_texture(shadow_rt.texture.id)
    shadow_map_loc = pr.get_shader_location(shader, "shadowMap")
    pr.rl_set_uniform(shadow_map_loc, pr.ffi.new("int *", shadow_slot), pr.SHADER_UNIFORM_INT, 1)
    shadow_map_size = pr.get_shader_location(shader, "shadowMapSize")
    pr.rl_set_uniform(shadow_map_size, pr.ffi.new("int *", size), pr.SHADER_UNIFORM_INT, 1)

    return shadow_rt


def update_shadow(shader, shadow_shader, shadow_rt, cube_model, light_cam, maze, agent, player, target, light_dir):

    light_cam.position = pr.vector3_add(target, pr.vector3_scale(light_dir, -15.0))
    light_cam.target = target

    pr.begin_texture_mode(shadow_rt)
    pr.clear_background(pr.WHITE)
    cube_model.materials[0].shader = shadow_shader
    pr.begin_mode_3d(light_cam)

    light_view = pr.rl_get_matrix_modelview()
    light_proj = pr.rl_get_matrix_projection()

    for i in range(maze.size):
        for j in range(maze.size):
            if maze.maze[i][j] != 0:
                height = maze.heights[i][j]
                pr.draw_model_ex(cube_model, (i + 0.5, 0.5 * height, j + 0.5), (0, 1, 0), 0, (1, height, 1), maze.colors[i][j])

    pr.draw_capsule_wires(
        (maze.exit[0] + 0.5, 0.36, maze.exit[1] + 0.5), (maze.exit[0] + 0.5, 0.70, maze.exit[1] + 0.5), 0.35, 10, 4, pr.BLACK
    )
    for item in [agent, player]:
        pr.draw_capsule((item.pos.x, 0.1, item.pos.z), (item.pos.x, 0.5, item.pos.z), 0.25, 10, 4, pr.BLACK)

    pr.end_mode_3d()
    cube_model.materials[0].shader = shader
    pr.end_texture_mode()

    light_view_proj = pr.matrix_multiply(light_view, light_proj)
    light_vp_loc = pr.get_shader_location(shader, "lightVP")
    pr.set_shader_value_matrix(shader, light_vp_loc, light_view_proj)


asyncio.run(main())