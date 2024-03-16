# from pathlib import Path

# import yaml
# from dagster import Definitions, ScheduleDefinition, asset, job

# from src.models.config import Config as UserConfig
# from src.jobs.sync_ical import sync_icalendar


# @asset
# def user_config() -> UserConfig:
#     """
#     User config yaml file.
#     """

#     with open(Path(__file__).parents[1] / "config" / "config.yaml", "r") as f:
#         config = UserConfig.from_dict(yaml.safe_load(f))
#     return config

# @job(config=)
# def myjob():
#     ...

# # schedule = ScheduleDefinition(
# #     cron_schedule="*/1 * * * *",
# # )

# defs = Definitions(
#     assets=[user_config],
#     # schedules=[schedule],
# )
